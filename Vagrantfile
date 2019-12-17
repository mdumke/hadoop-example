# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vbguest.auto_update = false
  config.vm.box = 'generic/ubuntu1804'
  config.ssh.insert_key = false
  config.vm.synced_folder '.', '/vagrant', disabled: true

  config.vm.hostname = 'hadoop'
  config.vm.network :private_network, ip: '192.168.60.2'

  config.vm.provider 'virtualbox' do |vb|
    vb.memory = '4096'
    vb.customize ['modifyvm', :id, '--natdnshostresolver1', 'on']
    vb.customize ['modifyvm', :id, '--ioapic', 'on']
  end

  config.vm.provision 'ansible' do |ansible|
    ansible.playbook = 'hadoop-single-node.yml'
    ansible.limit = 'hadoop'
    ansible.compatibility_mode = '2.0'
    ansible.inventory_path = 'inventory.cfg'
    ansible.extra_vars = {
      ansible_ssh_user: 'vagrant',
      ansible_ssh_private_key_file: '~/.vagrant.d/insecure_private_key'
    }
  end
end
