Name:           libfprint-goodixtls
Version:        1.94.9
Release:        6%{?dist}
Summary:        libfprint with the Goodix 5110 TLS driver (SIGFM matcher + external PSK)

License:        LGPL-2.1-or-later
URL:            https://github.com/iHat3Microsoft/libfprint-27c6-5110
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  pkgconfig(gusb)
BuildRequires:  pkgconfig(gudev-1.0)
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(gnutls)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  nss-devel
BuildRequires:  pkgconfig(udev)
BuildRequires:  pixman-devel

# Drop-in replacement for the stock libfprint: provides the same soname so
# fprintd keeps working.
Provides:       libfprint = %{version}-%{release}
Conflicts:      libfprint
Obsoletes:      libfprint < 1.94.100-999

%description
The buxel/libfprint fork (as consolidated by iHat3Microsoft/libfprint-27c6-5110,
libfprint v1.94.9) with the goodixtls511 driver for the Goodix 27c6:5110 sensor.
Matching uses the pure-C SIGFM algorithm (FAST-9 + BRIEF-256) instead of NBIS,
which is far more reliable on this small sensor. Carries a local patch so the
32-byte TLS PSK is read from /etc/goodix-fp/psk.bin (root-only), letting a sensor
provisioned by the stock Windows driver work without reflashing. Builds the
default driver set, so other supported readers keep working too.

%prep
%autosetup -n %{name}-%{version}

%build
%meson -Ddrivers=default -Dgoodixtls=enabled -Dintrospection=false -Ddoc=false -Dgtk-examples=false -Dinstalled-tests=false
%meson_build

%install
%meson_install

%files
%license COPYING
%{_libdir}/libfprint-2.so
%{_libdir}/libfprint-2.so.2
%{_libdir}/libfprint-2.so.2.*
%{_libdir}/pkgconfig/libfprint-2.pc
%{_includedir}/libfprint-2/
%{_datadir}/metainfo/org.freedesktop.libfprint.metainfo.xml
/usr/lib/udev/hwdb.d/*libfprint*.hwdb
/usr/lib/udev/rules.d/*libfprint*.rules

%changelog
* Tue Nov 10 2026 hkoeck - 1.94.9-6
- sigfm: keep the strongest keypoints instead of the topmost ones and raise the
  cap to 256, so the half-resolution pyramid level is no longer cut off by an
  arbitrary scan line.
- goodix5xx: CLAHE between the percentile squash and the unsharp mask. Measured
  on 27c6:5110 with the same enrolment procedure, match scores went from
  16/7/13 to 28/11/13 inliers against a 7-inlier threshold - the margin grows,
  the hit zone does not.
- goodix5xx: adaptive template study. A probe confirmed by an enrolled sample
  with a clear margin is appended to a 0600 sidecar beside the print and
  considered after the enrolled samples; at most 16 are kept, oldest out, tied
  to the enrolment by a sha256 digest so re-enrolling discards them. An unlock
  where every enrolled sample failed (best 4/7) was carried by a learned sample
  at 21/7.
* Wed Oct 28 2026 hkoeck - 1.94.9-5
- goodixtls: forward a cancellation from the TLS-established command instead of
  dropping it, so a cancel in its 10 ms window cannot leave the init SSM
  waiting for a finger (buxel/libfprint#3 review by fistboom).

* Mon Oct 26 2026 hkoeck - 1.94.9-4
- goodixtls: replace the local cancel handler with the upstream one from
  buxel/libfprint#3, which fixes the same hang and also propagates TLS
  handshake failures.

* Mon Oct 26 2026 hkoeck - 1.94.9-3
- goodixtls: implement the cancel handler. An interrupted scan left the
  infinite bulk-in read running, so fprintd never released the device and
  every later verify failed with "Device was already claimed".

* Fri Oct 17 2026 hkoeck - 1.94.9-2
- verify/identify: report the match on touch (skip FDT_UP lift wait).

* Fri Oct 16 2026 hkoeck - 1.94.9-1
- Switch to the SIGFM-matcher driver (buxel/iHat3Microsoft), external PSK.
