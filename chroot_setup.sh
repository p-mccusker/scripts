#!/bin/bash

#ROOT_DEV=$2
#BOOT_DEV=$3

MNT_DIR="/mnt/gentoo"

while getopts r:b:m: flag
do
	case "${flag}" in
		r) ROOT_DEV=${OPTARG};;
		b) BOOT_DEV=${OPTARG};;
		m) MNT_DIR=${OPTARG};;
	esac
done
echo "Using Root Device: $ROOT_DEV";
echo "Using Boot Device: $BOOT_DEV";

mkdir -p /mnt/gentoo
mount $ROOT_DEV $MNT_DIR
cd $MNT_DIR

mount --types proc /proc $MNT_DIR/proc 
mount --rbind /sys $MNT_DIR/sys 
mount --make-rslave $MNT_DIR/sys 
mount --rbind /dev $MNT_DIR/dev
mount --make-rslave $MNT_DIR/dev
mount --bind /run $MNT_DIR/run 
mount --make-slave $MNT_DIR/run

test -L /dev/shm && rm /dev/shm && mkdir /dev/shm
mount --types tmpfs --options nosuid,nodev,noexec shm /dev/shm 
chmod 1777 /dev/shm /run/shm

chroot /mnt/gentoo /bin/bash 
source /etc/profile 
export PS1="(chroot) ${PS1}"

mount $BOOT_DEV /boot
