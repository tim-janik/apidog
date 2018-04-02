# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0

# User configurable installation locations
prefix = $(HOME)
bindir = $(prefix)/bin
ifeq ($(prefix),$(HOME))
libexecdir = $(prefix)/.local
else
libexecdir = $(prefix)/libexec
endif
mpexecdir = $(libexecdir)/apidog

# Project specific installation files and directories
auxdir = $(mpexecdir)/aux
auxdir_files = $(strip		\
	aux/CComment.py		\
	aux/Doxyfile		\
	aux/FromJson.py		\
	aux/FromXml.py		\
	aux/html.py		\
	aux/__init__.py		\
	aux/Markdown.py		\
	aux/Node.py		\
	aux/run-doxygen		\
	aux/run-jsdoc		\
	aux/tags_glib.py	\
	aux/tags_susv4.py	\
)
auxdir_filesF = $(notdir $(auxdir_files))

Q = $(if $(findstring 1, $(V)) ,, @)
QVERBOSE = $(if $(findstring 1, $(V)) ,--verbose,)
INSTALL = install

all:
	$(Q) echo prefix=$(prefix)
	$(Q) echo mpexecdir=$(mpexecdir)

install:
	$(INSTALL) -d -m 755 '$(DESTDIR)$(bindir)'
	$(Q) sed $(SED_INSTALLCONFIG) apidog >.apidog.installable
	$(INSTALL) -m 755 .apidog.installable '$(DESTDIR)$(bindir)/apidog'
	$(Q) rm -f .apidog.installable
	$(INSTALL) -d -m 755 '$(DESTDIR)$(auxdir)'
	cd aux/ && \
	  $(INSTALL) $(auxdir_filesF) '$(DESTDIR)$(auxdir)'
SED_INSTALLCONFIG = '1,24s|^INSTALLCONFIG\b.*|INSTALLCONFIG = [ "$(mpexecdir)" ]|'
uninstall:
	rm -f '$(DESTDIR)$(bindir)/apidog'
	(cd $(DESTDIR)$(auxdir) && rm -f $(auxdir_filesF))
	rm -rf $(DESTDIR)$(auxdir)/__pycache__/

check: test-cxx


test-cxx:
	aux/run-doxygen $(QVERBOSE) tests/
	aux/FromXml.py $(QVERBOSE) build/xml > tests/tests.md
	pandoc $(QVERBOSE) -S -s --section-divs --number-sections tests/tests.md > tests/tests.html

# --css styles.css
