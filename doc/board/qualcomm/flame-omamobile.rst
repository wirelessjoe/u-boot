.. SPDX-License-Identifier: GPL-2.0+

Google Pixel 4 standalone Omarchy development configuration
==========================================================

Based on Andrew Gigena's flame tree at
0c42ac323aea8368b0624e405ded403351022df2 from
https://gitlab.com/andrewgigena/u-boot.

Build with ``qcom_flame_omamobile_defconfig`` and an aarch64 cross compiler.
The volatile default environment waits two seconds, scans UFS, resolves GPT
``userdata``, loads ``/boot/omamobile/boot.img`` from ext4 and runs ``bootm``.
A successful boot does not wait for USB. Failure enters download-only fastboot.
No environment is saved. Android ABL, not this U-Boot fastboot implementation,
is used for separately approved writes of ``boot_b`` and ``userdata``.

The USB role is peripheral, matching the tested flame setup. The simplefb
probe defaults missing rotation to zero, honors row stride and rejects layouts
outside the framebuffer. ``python3 test/video/flame_simplefb_probe.py`` runs
the real probe in host fixtures with ASan/UBSan, including missing rotation,
padded rows, overflow and invalid buffer bounds.

This configuration removes unused EFI/FAT-write, DFU and USB mass-storage
facilities and their menu entries. It disables fastboot flashing and OEM run
commands. Its automatic boot path performs only partition lookup and ext4
reads. This is not a hardware storage guard: interactive U-Boot commands such
as ``scsi write`` must never be used on protected phone storage. Firmware and
calibration data are not part of this tree.

Validation boundaries
---------------------

The driver change at cefacc22 and the same USB role, two-second wait and
userdata/ext4/bootm path passed temporary and installed boots on Pixel 4,
including normal restarts, deliberate crash recovery and unplugged restart.
The tested installed image used a larger inherited configuration. This
configuration's smaller menu and removal of unused write facilities, plus the
invalid-width arithmetic guard, were built and checked on the host only.
They require a fresh owner-approved RAM boot before any new image is flashed.
The earlier spontaneous runtime-reset cause remains unproven. See the dated
Omarchy Mobile native results for the full device test limits and recovery
requirements. No device image or owner data is distributed with this source.
