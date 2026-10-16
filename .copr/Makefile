# COPR "make srpm" entry point.
# COPR runs:  make -f .copr/Makefile srpm outdir=<dir>
# We check out the libfprint submodule, apply the local PSK-from-file patch,
# pack a release tarball, and build the SRPM from rpm/libfprint-goodixtls.spec.
NAME = libfprint-goodixtls
VERSION = 1.94.9
outdir ?= $(CURDIR)

srpm:
	git submodule update --init --recursive
	cd libfprint-fork && git apply -p1 "$(CURDIR)/rpm/0001-psk-from-file.patch"
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
