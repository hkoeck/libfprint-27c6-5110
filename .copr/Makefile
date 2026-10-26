# COPR "make srpm" entry point.
# COPR runs:  make -f .copr/Makefile srpm outdir=<dir>
# We check out the libfprint submodule, apply the local PSK-from-file patch,
# pack a release tarball, and build the SRPM from rpm/libfprint-goodixtls.spec.
NAME = libfprint-goodixtls
VERSION = 1.94.9
outdir ?= $(CURDIR)

srpm:
	# COPR clones the repo with --recursive on the host, so the submodule is
	# already populated and `git` is NOT available in the srpm buildroot. Only
	# fetch submodules when missing (i.e. a plain local clone), and apply the
	# patch with patch(1), which IS present in the buildroot.
	test -f libfprint-fork/meson.build || git submodule update --init --recursive
	patch -p1 -d libfprint-fork < rpm/0001-psk-from-file.patch
	patch -p1 -d libfprint-fork < rpm/0002-report-on-touch.patch
	patch -p1 -d libfprint-fork < rpm/0003-cancel-read-loop-on-abort.patch
	rm -rf /tmp/$(NAME)-$(VERSION)
	mkdir -p /tmp/$(NAME)-$(VERSION)
	tar --exclude=.git --exclude=./build -C libfprint-fork -cf - . \
	  | tar -C /tmp/$(NAME)-$(VERSION) -xf -
	tar -C /tmp -czf "$(outdir)/$(NAME)-$(VERSION).tar.gz" $(NAME)-$(VERSION)
	rpmbuild -bs rpm/$(NAME).spec \
	  --define "_sourcedir $(outdir)" \
	  --define "_srcrpmdir $(outdir)" \
	  --define "_specdir $(CURDIR)/rpm" \
	  --define "_builddir $(outdir)/_b" \
	  --define "_rpmdir $(outdir)/_r"
