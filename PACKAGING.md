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

## Getting the PSK (per machine, one-time)

The PSK is secret and device-specific — it is **not** shipped in the package.
Recover it from the Windows install that provisioned the sensor (DPAPI), or let
Linux provision a fresh one. See `goodix-fp/NOTES.md` in the notebook repo for
the full procedure, then:

    sudo install -Dm600 psk.bin /etc/goodix-fp/psk.bin

## Build locally

    git submodule update --init --recursive
    make -f .copr/Makefile srpm outdir=/tmp/out
    sudo dnf install /tmp/out/libfprint-goodixtls-*.src.rpm   # or rpmbuild --rebuild

## COPR

Point a COPR package at this repo (SCM / "make srpm" method); COPR rebuilds on
each push and `dnf copr enable <user>/libfprint-goodixtls` keeps it updated.
