%{?scl:%scl_package cargo-vendor}
%{!?scl:%global pkg_name %{name}}

# Only x86_64 and i686 are Tier 1 platforms at this time.
# https://forge.rust-lang.org/platform-support.html
#global rust_arches x86_64 i686 armv7hl aarch64 ppc64 ppc64le s390x
%global rust_arches x86_64 i686 aarch64 ppc64 ppc64le s390x

%if 0%{?rhel} && !0%{?epel}
%bcond_without bundled_libgit2
%else
%bcond_with bundled_libgit2
%endif

Name:           %{?scl_prefix}cargo-vendor
Version:        0.1.12
Release:        1%{?dist}
Summary:        Cargo subcommand to vendor crates.io dependencies
License:        ASL 2.0 or MIT
URL:            https://github.com/alexcrichton/cargo-vendor
ExclusiveArch:  %{rust_arches}

Source0:        %{url}/archive/%{version}/%{pkg_name}-%{version}.tar.gz

# Use vendored crate dependencies so we can build offline.
# Created using cargo-vendor itself!
# It's so big because some of the -sys crates include the C library source they
# want to link to.  With our -devel buildreqs in place, they'll be used instead.
# FIXME: These should all eventually be packaged on their own!
Source100:      %{pkg_name}-%{version}-vendor.tar.xz

BuildRequires:  %{?scl_prefix}rust
BuildRequires:  %{?scl_prefix}cargo

# Indirect dependencies for vendored -sys crates above
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  libcurl-devel
BuildRequires:  libssh2-devel
BuildRequires:  openssl-devel
BuildRequires:  zlib-devel
BuildRequires:  pkgconfig

%if %with bundled_libgit2
Provides:       bundled(libgit2) = 0.25.0
%else
BuildRequires:  libgit2-devel >= 0.24
%endif

# It only supports being called as a subcommand, "cargo vendor"
Requires:       %{?scl_prefix}cargo

%{?scl:Requires:%scl_runtime}

%description
This is a Cargo subcommand which vendors all crates.io dependencies into a
local directory using Cargo's support for source replacement.


%prep

# cargo-vendor sources
%setup -q -n %{pkg_name}-%{version}

# vendored crates
%setup -q -n %{pkg_name}-%{version} -T -D -a 100

# define the offline registry
%global cargo_home $PWD/.cargo
mkdir -p %{cargo_home}
cat >.cargo/config <<EOF
[source.crates-io]
registry = 'https://github.com/rust-lang/crates.io-index'
replace-with = 'vendored-sources'

[source.vendored-sources]
directory = '$PWD/vendor'
EOF

# This should eventually migrate to distro policy
# Enable optimization, debuginfo, and link hardening.
%global rustflags -Copt-level=3 -Cdebuginfo=2
%if 0%{?fedora} || (0%{?rhel} >= 7)
%global rustflags %{?rustflags} -Clink-arg=-Wl,-z,relro,-z,now
%endif

%build

%if %without bundled_libgit2
# convince libgit2-sys to use the distro libgit2
export LIBGIT2_SYS_USE_PKG_CONFIG=1
%endif

# use our offline registry and custom rustc flags
export CARGO_HOME="%{cargo_home}"
export RUSTFLAGS="%{rustflags}"

%{?scl:scl enable %scl - << \EOF}
set -ex

# cargo-vendor doesn't use a configure script, but we still want to use
# CFLAGS in case of the odd C file in vendored dependencies.
%{?__global_cflags:export CFLAGS="%{__global_cflags}"}
%{!?__global_cflags:%{?optflags:export CFLAGS="%{optflags}"}}
%{?__global_ldflags:export LDFLAGS="%{__global_ldflags}"}

cargo build --release

%{?scl:EOF}


%install
export CARGO_HOME="%{cargo_home}"
export RUSTFLAGS="%{rustflags}"

%{?scl:scl enable %scl - << \EOF}
set -ex

cargo install --root %{buildroot}%{_prefix}
rm -f %{buildroot}%{_prefix}/.crates.toml

%{?scl:EOF}


#check
# the tests don't work offline


%files
%license LICENSE-APACHE LICENSE-MIT
%doc README.md
%{_bindir}/cargo-vendor


%changelog
* Mon Sep 11 2017 Josh Stone <jistone@redhat.com> - 0.1.12-1
- Update to 0.1.12.

* Mon Jul 24 2017 Josh Stone <jistone@redhat.com> - 0.1.11-1
- Update to 0.1.11.

* Thu Jun 15 2017 Josh Stone <jistone@redhat.com> - 0.1.7-1
- Initial packaging.
