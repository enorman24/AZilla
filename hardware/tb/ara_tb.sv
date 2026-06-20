// Copyright 2021-2025 ETH Zurich and University of Bologna.
// Solderpad Hardware License, Version 0.51, see LICENSE for details.
// SPDX-License-Identifier: SHL-0.51
//
// Author: Matheus Cavalcante <matheusd@iis.ee.ethz.ch>
// Description:
// Top level testbench module.

`define STRINGIFY(x) `"x`"

module ara_tb;

  /*****************
   *  Definitions  *
   *****************/

  `ifndef VERILATOR
    timeunit      1ns;
    timeprecision 1ps;
  `endif

  `ifdef VCS
    initial begin
      $fsdbDumpfile("waveform.fsdb");
      $fsdbDumpvars(0, "+struct", "+mda");
    end
  `endif

  `ifdef NR_LANES
  localparam NrLanes = `NR_LANES;
  `else
  localparam NrLanes = 0;
  `endif

  `ifdef NR_CLUSTERS
  localparam NrClusters = `NR_CLUSTERS;
  `else
  localparam NrClusters = 0;
  `endif

  localparam ClockPeriod  = 1ns;
  // Axi response delay [ps]
  localparam int unsigned AxiRespDelay = 200;

  localparam AxiAddrWidth          = 64;
  localparam AxiWideDataWidth      = 32 * NrLanes * NrClusters;
  localparam ClusterAxiDataWidth   = 32 * NrLanes;
  localparam AxiWideBeWidth = AxiWideDataWidth / 8;

  /********************************
   *  Clock and Reset Generation  *
   ********************************/

  logic clk;
  logic rst_n;

  // Controlling the reset
  initial begin
    clk   = 1'b0;
    rst_n = 1'b0;

    // Synch reset for TB memories
    repeat (10) #(ClockPeriod/2) clk = ~clk;
    clk = 1'b0;

    // Asynch reset for main system
    repeat (5) #(ClockPeriod);
    rst_n = 1'b1;
    repeat (5) #(ClockPeriod);

    // Start the clock
    forever #(ClockPeriod/2) clk = ~clk;
  end

  /*********
   *  DUT  *
   *********/

  logic [63:0] exit;

  // This TB must be implemented in C for integration with Verilator.
  // In order to Verilator to understand that the ara_testharness module is the top-level,
  // we do not instantiate it when Verilating this module.
  `ifndef VERILATOR
  ara_testharness #(
    .NrLanes     (NrLanes         ),
    .NrClusters  (NrClusters      ),
    .AxiAddrWidth(AxiAddrWidth    ),
    .AxiDataWidth(AxiWideDataWidth),
    .ClusterAxiDataWidth(ClusterAxiDataWidth),
    .AxiRespDelay(AxiRespDelay    )
  ) dut (
    .clk_i (clk  ),
    .rst_ni(rst_n),
    .exit_o(exit )
  );
  `endif

  /*************************
   *  DRAM Initialization  *
   *************************/

  // Program preload now happens inside i_dram (tc_sram.sv) via
  // $readmemh(+DRAM_INIT_FILE, init_val) at time zero; the `sram <= init_val` reset copy
  // carries it into the live array. Generate the vmem with hardware/scripts/elf2vmem.py.

  typedef logic [AxiWideDataWidth-1:0] data_t;

`ifndef TARGET_GATESIM

  /*************************
   *  PRINT STORED VALUES  *
   *************************/

  // This is useful to check that the ideal dispatcher simulation was correct

`ifndef IDEAL_DISPATCHER
  localparam OutResultFile = "../gold_results.txt";
`else
  localparam OutResultFile = "../id_results.txt";
`endif

  int fd;

  data_t                     ara_w;
  logic [AxiWideBeWidth-1:0] ara_w_strb;
  logic                      ara_w_valid;
  logic                      ara_w_ready;

  // Avoid dumping what it's not measured, e.g. cache warming
  logic dump_en_mask;

  initial begin
    fd = $fopen(OutResultFile, "w");
    $display("Dump results on %s", OutResultFile);
  end

  /*
  assign ara_w       = dut.i_ara_soc.i_system.i_ara.i_vlsu.axi_req.w.data;
  assign ara_w_strb  = dut.i_ara_soc.i_system.i_ara.i_vlsu.axi_req.w.strb;
  assign ara_w_valid = dut.i_ara_soc.i_system.i_ara.i_vlsu.axi_req.w_valid;
  assign ara_w_ready = dut.i_ara_soc.i_system.i_ara.i_vlsu.axi_resp.w_ready;
  */

  assign ara_w       = dut.i_ara_soc.i_system.i_ara_cluster.axi_req_o.w.data;
  assign ara_w_strb  = dut.i_ara_soc.i_system.i_ara_cluster.axi_req_o.w.strb;
  assign ara_w_valid = dut.i_ara_soc.i_system.i_ara_cluster.axi_req_o.w_valid;
  assign ara_w_ready = dut.i_ara_soc.i_system.i_ara_cluster.axi_resp_i.w_ready;

`ifndef IDEAL_DISPATCHER
  assign dump_en_mask = dut.i_ara_soc.hw_cnt_en_o[0];
`else
  // Ideal-Dispatcher system does not warm the scalar cache
  assign dump_en_mask = 1'b1;
`endif
  always_ff @(posedge clk)
    if (dump_en_mask)
      if (ara_w_valid && ara_w_ready)
        for (int b = 0; b < AxiWideBeWidth; b++)
          if (ara_w_strb[b])
            $fdisplay(fd, "%0x", ara_w[b*8 +: 8]);

`endif

  /*********
   *  EOC  *
   *********/

`ifndef TARGET_GATESIM
  for (genvar gc = 0; gc < NrClusters; gc++) begin : gen_fpu_disp_cluster
    for (genvar gl = 0; gl < NrLanes; gl++) begin : gen_fpu_disp_lane
      always @(posedge clk) begin
        if (exit[0] && !(exit >> 1)) begin
          $display("cluster-%0d-lane-%0d [fpu-cycles] : %d", gc, gl, int'(dut.i_ara_soc.i_system.i_ara_cluster.p_cluster[gc].i_ara_macro.i_ara.gen_lanes[gl].i_lane.i_vfus.i_vmfpu.fpu_gen.vfpu_cnt_q));
        end
      end
    end
  end
`endif

  always @(posedge clk) begin
    if (exit[0]) begin
      if (exit >> 1) begin
        $warning("Core Test ", $sformatf("*** FAILED *** (tohost = %0d)", (exit >> 1)));
      end else begin
`ifndef TARGET_GATESIM
        $display("[hw-cycles]: %d", int'(dut.runtime_buf_q));
        $display("[cva6-d$-stalls]: %d", int'(dut.dcache_stall_buf_q));
        $display("[cva6-i$-stalls]: %d", int'(dut.icache_stall_buf_q));
        $display("[cva6-sb-full]: %d", int'(dut.sb_full_buf_q));
`endif
        $info("Core Test ", $sformatf("*** SUCCESS *** (tohost = %0d)", (exit >> 1)));
      end

`ifndef TARGET_GATESIM
      $fclose(fd);
`endif
      $finish(exit >> 1);
    end
  end

// Dump VCD with a SW trigger
`ifdef VCD_DUMP

  /****************
  *  VCD DUMPING  *
  ****************/

`ifdef VCD_PATH
  string vcd_path = `STRINGIFY(`VCD_PATH);
`else
  string vcd_path = "../vcd/last_sim.vcd";
`endif

  localparam logic [63:0] VCD_TRIGGER_ON  = 64'h0000_0000_0000_0001;
  localparam logic [63:0] VCD_TRIGGER_OFF = 64'hFFFF_FFFF_FFFF_FFFF;

  event start_dump_event;
  event stop_dump_event;

  logic [63:0] event_trigger_reg;
  logic        dumping = 1'b0;

  assign event_trigger_reg =
           dut.i_ara_soc.i_ctrl_registers.event_trigger_o;

  initial begin
    $display("VCD_DUMP successfully defined\n");
  end

  always_ff @(posedge clk) begin
    if(event_trigger_reg == VCD_TRIGGER_ON && !dumping) begin
       $display("[TB - VCD] START DUMPING\n");
       -> start_dump_event;
       dumping = 1'b1;
    end
    if(event_trigger_reg == VCD_TRIGGER_OFF) begin
       -> stop_dump_event;
       $display("[TB - VCD] STOP DUMPING\n");
    end
  end

  initial begin
    @(start_dump_event);
    $dumpfile(vcd_path);
    $dumpvars(0, dut.i_ara_soc.i_system);
    $dumpon;

    #1 $display("[TB - VCD] DUMPING...\n");

    @(stop_dump_event)
    $dumpoff;
    $dumpflush;
    $finish;
  end

`endif

endmodule : ara_tb
