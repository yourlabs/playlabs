# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-18.04"
  config.ssh.insert_key = false
  config.ssh.forward_agent = true

  config.vm.network "private_network", ip: "192.168.168.168"

  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine, for debugging
    # vb.gui = true
    vb.memory = "4096"
    vb.cpus = 2
  end

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "playlabs/init.yml"
    ansible.become = true
    ansible.become_user = "root"
  end
end
