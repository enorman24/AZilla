#!/usr/bin/env bash

# Copyright 2021-2025 ETH Zurich and University of Bologna.
# Solderpad Hardware License, Version 0.51, see LICENSE for details.
# SPDX-License-Identifier: SHL-0.51
#
# Author: Samuel Riedel <sriedel@iis.ee.ethz.ch>

# Verilator: "Core Test" appears on the same line as the %Info prefix.
# VCS: $info/$warning emits the location header on one line, then the message
# on the next line.  Grep for "Core Test" directly to handle both simulators.
RET=$(grep 'Core Test' "$1" | grep -Poh -- '(?<=\(tohost = )-?[0-9]+(?=\))' | tail -n 1)
[[ -z "${RET}" ]] && echo "Simulation did not finish" && exit 1
echo "Simulation returned ${RET}"
[[ "${RET}" -eq 0 ]] && exit 0 || exit 1
