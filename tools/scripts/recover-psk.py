#!/usr/bin/env python3
"""Recover the Goodix 27c6:5110 TLS PSK from a vendor-provisioned sensor.

A sensor provisioned by Goodix's Windows driver uses a random 32-byte PSK that
the driver sealed with the machine's DPAPI key. To use the sensor on Linux
without reflashing it (which would break it in Windows), that key has to be
recovered once from the Windows install that provisioned it.

This reads only; it never writes to the sensor or to Windows. Point it at a
read-only mount of the Windows partition. The one step that touches Windows
credential storage - turning the machine DPAPI key into the decrypted master
key - is delegated to impacket (`pip install impacket`), the established tool
for it; this script does the Goodix-specific parsing and assembly around it.

Verified byte-for-byte against a sensor running in both OSes.

  python3 recover-psk.py --windows-mount /run/media/you/WINDOWS -o psk.bin
  sudo install -Dm600 psk.bin /etc/goodix-fp/psk.bin && sudo systemctl restart fprintd
"""
import argparse
import hashlib
import os
import subprocess
import sys

# gfspi.dll sub_26fe0: a constant baked into the driver (version 1.1.124.115).
ROOTKEY = bytes.fromhex("04e0b0f3f5598417dde298e467c795f7")


def derive_entropy(salt: bytes) -> bytes:
    h1 = hashlib.sha256(salt).digest()
    return h1[16:] + hashlib.sha256(h1[:16] + ROOTKEY).digest()


def masterkey_guid(blob: bytes) -> str:
    # The DPAPI blob names the master key that sealed it in its header.
    from impacket.dpapi import DPAPI_BLOB
    import struct
    raw = DPAPI_BLOB(blob)["GuidMasterKey"]
    d1, d2, d3 = struct.unpack("<IHH", raw[:8])
    return "%08x-%04x-%04x-%s-%s" % (d1, d2, d3, raw[8:10].hex(), raw[10:16].hex())


def run_impacket(args, tool):
    exe = os.path.join(os.path.dirname(sys.executable), tool)
    cmd = [exe] + args if os.path.exists(exe) else [sys.executable, "-m", "impacket.examples." + tool.removesuffix(".py")] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--windows-mount", required=True,
                    help="read-only mount of the Windows system partition")
    ap.add_argument("--cache", help="override path to Goodix_Cache.bin")
    ap.add_argument("-o", "--output", default="psk.bin", help="where to write the 32-byte PSK")
    ap.add_argument("--compare", help="an existing psk.bin to check the result against")
    args = ap.parse_args()

    try:
        import impacket  # noqa: F401
    except ImportError:
        sys.exit("impacket is required: pip install impacket")

    mount = args.windows_mount.rstrip("/")
    cache_path = args.cache or os.path.join(mount, "ProgramData", "Goodix", "Goodix_Cache.bin")
    system = os.path.join(mount, "Windows", "System32", "config", "SYSTEM")
    security = os.path.join(mount, "Windows", "System32", "config", "SECURITY")
    protect = os.path.join(mount, "Windows", "System32", "Microsoft", "Protect", "S-1-5-18")
    for p in (cache_path, system, security, protect):
        if not os.path.exists(p):
            sys.exit("not found (is this the Windows system partition?): " + p)

    cache = open(cache_path, "rb").read()
    if len(cache) < 40:
        sys.exit("Goodix_Cache.bin is too small: %d bytes" % len(cache))
    blob, salt = cache[:-8], cache[-8:]
    entropy = derive_entropy(salt)
    guid = masterkey_guid(blob)
    print("[*] master key:", guid)

    # The one step that reads Windows credential storage - decrypting the master
    # key from the machine DPAPI key - is delegated to impacket's dpapi.py.
    r = run_impacket(["masterkey", "-file", os.path.join(protect, guid),
                      "-system", system, "-security", security], "dpapi.py")
    key = next((ln.split("Decrypted key:")[1].strip()
                for ln in r.stdout.splitlines() if "Decrypted key:" in ln), None)
    if not key:
        sys.exit("could not decrypt the master key:\n" + r.stdout + r.stderr)

    # Unsealing the blob with that key + entropy is plain DPAPI; impacket's
    # library returns the raw bytes, no output scraping.
    from impacket.dpapi import DPAPI_BLOB
    try:
        psk = DPAPI_BLOB(blob).decrypt(bytes.fromhex(key[2:] if key.startswith("0x") else key), entropy)[:32]
    except Exception as e:
        sys.exit("unprotect failed: %s" % e)
    if len(psk) != 32:
        sys.exit("unprotect did not yield a 32-byte PSK (got %d)" % len(psk))

    open(args.output, "wb").write(psk)
    os.chmod(args.output, 0o600)
    print("[+] wrote", args.output, "(" + psk.hex() + ")")

    if args.compare:
        want = open(args.compare, "rb").read()
        print("[+] matches " + args.compare if want == psk
              else "[!] DOES NOT match " + args.compare)
    else:
        print("    install it:  sudo install -Dm600 %s /etc/goodix-fp/psk.bin" % args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
