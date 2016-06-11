# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "adaptiveme/vivid64"
  #config.vm.network :private_network, ip: "192.168.50.26"

  #config.vm.network "forwarded_port", guest: 8002, host: 8002

  config.vm.provider "virtualbox" do |vb|
    #Allow symbolic link inside shared directory
    vb.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/v-root", "1"]
    vb.memory = "1024"
  end

  config.vm.provision "shell", inline: <<-SHELL
    sudo apt-get update
    sudo apt-get install -y python3 emacs git build-essential python3-pip zip
  SHELL

end
