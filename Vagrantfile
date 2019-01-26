# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-18.04"
  config.ssh.insert_key = false
  config.ssh.forward_agent = true

  if ENV['VAGRANT_TYPE'] == 'dhcp'
    config.vm.network "private_network", type: "dhcp"
  else
    config.vm.network "private_network", ip: "192.168.168.168"
  end

  config.vm.provider "virtualbox" do |vb|
    vb.gui = ENV['VAGRANT_GUI']
    vb.memory = "4096"
    vb.cpus = 2
  end

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "playlabs/init.yml"
    ansible.become = true
    ansible.become_user = "root"
  end
end
