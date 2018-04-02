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

Q = $(if $(findstring 1, $(V)) ,, @)

all:
	$(Q) echo prefix=$(prefix)
	$(Q) echo mpexecdir=$(mpexecdir)

