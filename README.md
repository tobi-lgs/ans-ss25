# Advanced Networked Systems SS25

This repository contains code skeleton for the labs of Advanced Networked Systems SS25 at Paderborn University, Germany. There are in total three labs, which will be released one by one throughout the semester. For more details, please refer to the lab descriptions released on PANDA.

## Getting Started

### Setup and Installation

The first step is to adjust the `Vagrantfile`.

Run `vagrant up` in the root directory of the repository to install and start the virtual machine. Then run `vagrant ssh` to log into the virtual machine. Check these fields:

```Vagrantfile
# Specify the memory and CPU cores for the VM
  config.vm.provider :virtualbox do |vb|
    vb.memory = 8192    # 8 GB
    vb.cpus = 4        # 4 cores
  end
```

### Accessing the VM

Alternatively, you can use the following command to log in directly:

```powershell
ssh -Y -i "./.vagrant/machines/default/virtualbox/private_key" -p 2222 -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o PubkeyAcceptedKeyTypes=+ssh-rsa -o HostKeyAlgorithms=+ssh-rsa vagrant@127.0.0.1
```

Then enter `export DISPLAY=localhost:10.0` into the terminal of the VM to enable X11 forwarding. This will allow you to run GUI applications from the VM on your local machine. Test with `xclock` or `xeyes`.
To make the last step permanent, edit the `~/.bashrc` file in the VM with `nano ~/.bashrc` and add the line `export DISPLAY=localhost:10.0` at the end of the file. This will set the `DISPLAY` variable every time you log in to the VM.

Or configure Putty like described [here](https://jcook0017.medium.com/how-to-enable-x11-forwarding-in-windows-10-on-a-vagrant-virtual-box-running-ubuntu-d5a7b34363f).

>Remember to launch Xming before running the SSH command.

### Stopping the VM

Run `vagrant halt` to stop the VM. This will save the current state of the VM and shut it down. You can then start it again with `vagrant up`.

### Troubleshooting

If this does not work, please check the following:

- Make sure you have installed VirtualBox and Vagrant on your machine. Check for updates.
- Check if the VirtualBox Guest Additions are installed in the VM and match the version of your VirtualBox installation.

#### Error: `vagrant@127.0.0.1: Permission denied (publickey).`

Reason:

```powershell
ssh -i "C:/git_workspace/ans-ss25/.vagrant/machines/default/virtualbox/private_key" -p 2222 -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o PubkeyAcceptedKeyTypes=+ssh-rsa -o HostKeyAlgorithms=+ssh-rsa vagrant@127.0.0.1
Warning: Permanently added '[127.0.0.1]:2222' (ED25519) to the list of known hosts.
Bad permissions. Try removing permissions for user: VORDEFINIERT\\Benutzer (S-1-5-32-545) on file C:/git_workspace/ans-ss25/.vagrant/machines/default/virtualbox/private_key.
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions for 'C:/git_workspace/ans-ss25/.vagrant/machines/default/virtualbox/private_key' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
Load key "C:/git_workspace/ans-ss25/.vagrant/machines/default/virtualbox/private_key": bad permissions
```

Solution: Change the permissions of the private key file to be readable only by the user. You can do this by running the following command in PowerShell:

```powershell
$privateKey = "C:\git_workspace\ans-ss25\.vagrant\machines\default\virtualbox\private_key"
icacls $privateKey /inheritance:r
icacls $privateKey /grant:r "$($env:USERNAME):(R)"
```

#### Error `Exception: Error creating interface pair (s1-eth3,s3-eth2): RTNETLINK answers: File exists`

Reason: Mininet failed previously and did not clean up properly.

Solution: Manually delete the links, e.g.:

```bash
sudo ip link delete s1-eth3
sudo ip link delete s2-eth2
```

### Mininet Commands

- ping all hosts: `pingall`
- ping between hosts: `h1 ping -c1 h2`
- iperf between hosts: `iperf h1 h2`
- print arp table of a host: `h1 arp -n`
