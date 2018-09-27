apt-get -y install software-properties-common
add-apt-repository -y ppa:alexlarsson/flatpak
add-apt-repository -y ppa:gophers/archive
apt-add-repository -y ppa:projectatomic/ppa
apt-get -y -qq update
apt-get -y install bats btrfs-tools git libapparmor-dev libdevmapper-dev libglib2.0-dev libgpgme11-dev libostree-dev libseccomp-dev libselinux1-dev skopeo go-md2man libpam-cgfs uidmap
apt-get -y install golang-1.8
mkdir -p ~/buildah
cd ~/buildah
export GOPATH=`pwd`
test -d ./src/github.com/containers/buildah || git clone https://github.com/containers/buildah ./src/github.com/containers/buildah
cd ./src/github.com/containers/buildah
PATH=/usr/lib/go-1.8/bin:$PATH make runc all TAGS="apparmor seccomp"
sudo make install install.runc
buildah --help
