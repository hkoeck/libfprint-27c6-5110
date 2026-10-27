# Packaging: libfprint-goodixtls for the Goodix 27c6:5110

This fork of [iHat3Microsoft/libfprint-27c6-5110](https://github.com/iHat3Microsoft/libfprint-27c6-5110)
adds RPM packaging + COPR support and one local patch:

- `rpm/0001-psk-from-file.patch` — the GnuTLS PSK callback reads the 32-byte TLS
  PSK from `/etc/goodix-fp/psk.bin` (root 600) instead of the hard-coded
  all-zeros factory PSK. This lets a sensor **provisioned by the stock vendor
  (Windows) driver** work without reflashing it with goodix-fp-dump. If the file
  is absent it falls back to the factory PSK (unchanged behaviour).
- `rpm/libfprint-goodixtls.spec` — builds the default driver set with the
  goodixtls511 driver (SIGFM matcher) and replaces the stock `libfprint`
  (`Provides` the soname, `Obsoletes`/`Conflicts: libfprint`).
- `.copr/Makefile` — COPR `make srpm` target: inits the submodule, applies the
  patch, tars a release, builds the SRPM.

## Do I need the PSK file at all?

The sensor speaks TLS-PSK, and which key it expects depends on how it was
provisioned. Only the second case needs the file:

**The sensor was reflashed by goodix-fp-dump.** That is the community route and
it writes the all-zeros factory PSK. The driver uses that key by default, so
the package works as installed and `/etc/goodix-fp/psk.bin` is not needed.

**The sensor is still provisioned by the vendor's Windows driver.** Then the key
is a random 32 bytes that the Windows driver generated and sealed; the sensor
accepts nothing else. Reflashing would work but takes the sensor away from
Windows. Putting the real key in `/etc/goodix-fp/psk.bin` lets both systems use
the sensor, and Linux never writes to it.

## Getting the PSK from a vendor-provisioned sensor (one-time, per machine)

**You do not need to boot Windows, but the Windows installation that provisioned
the sensor has to still exist.** The key is sealed with that installation's
machine DPAPI key. Reinstalled, reset or wiped Windows means the master key is
gone and the sealed key is unrecoverable — then the only way forward is to
reflash with goodix-fp-dump (and Windows loses the sensor until its driver
provisions it again).

`tools/scripts/recover-psk.py` does all of this; point it at the mounted
Windows partition (needs `pip install impacket`):

    python3 tools/scripts/recover-psk.py --windows-mount /run/media/you/WINDOWS -o psk.bin
    sudo install -Dm600 psk.bin /etc/goodix-fp/psk.bin
    sudo systemctl restart fprintd

It reads only, never writes to the sensor or to Windows, and was verified
byte-for-byte against a sensor running in both OSes. What it does, step by step:

1. Take the sealed blob: `C:\ProgramData\Goodix\Goodix_Cache.bin`, or read
   slot `0xbb010002` from the sensor. Last 8 bytes are the salt, the rest is a
   DPAPI blob.
2. Derive the 48-byte entropy from that salt (a fixed Goodix routine):
   `rk = 04e0b0f3f5598417dde298e467c795f7`, `h1 = SHA256(salt)`,
   `entropy = h1[16:] + SHA256(h1[:16] + rk)`. `rk` is a constant baked into
   gfspi.dll 1.1.124.115.
3. Get the `DPAPI_SYSTEM` LSA secret from the `SYSTEM` + `SECURITY` hives, use it
   to decrypt the master key the blob names under `Windows\System32\Microsoft\
   Protect\S-1-5-18\`. impacket covers this.
4. Unseal the blob with that key and the entropy → the 32-byte PSK.
5. Verify before trusting it: `SHA256(SecWhiteEncrypt(PSK))` must equal the hash
   in sensor slot `0xbb020003`. If it does not match, the key belongs to an
   older Windows install. (`SecWhiteEncrypt` is the Goodix whitebox transform;
   a bit-exact implementation of it is still TODO in this repo.)

Then:

    sudo install -Dm600 psk.bin /etc/goodix-fp/psk.bin
    sudo systemctl restart fprintd

A wrong or truncated file is not fatal: the driver warns and falls back to the
factory PSK.

## Build locally

    git submodule update --init --recursive
    make -f .copr/Makefile srpm outdir=/tmp/out
    sudo dnf install /tmp/out/libfprint-goodixtls-*.src.rpm   # or rpmbuild --rebuild

## COPR

Point a COPR package at this repo (SCM / "make srpm" method); COPR rebuilds on
each push and `dnf copr enable <user>/libfprint-goodixtls` keeps it updated.
