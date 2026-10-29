`timescale 1ns / 1ps

module tb_top;

  //clock and reset signal declaration
  logic tb_clk, reset;
  logic [31:0] tb_WB_Data;

  logic [4:0] reg_num;
  logic [31:0] reg_data;
  logic reg_write_sig;
  logic wr;
  logic rd;
  logic [8:0] addr;
  logic [31:0] wr_data;
  logic [31:0] rd_data;

  localparam CLKPERIOD = 10;
  localparam CLKDELAY = CLKPERIOD / 2;

  // Icarus flow: vvp -n tb.vvp +vcd=build/pipeline.vcd
  reg [1023:0] vcd_file;

  riscv riscV (
      .clk(tb_clk),
      .reset(reset),
      .WB_Data(tb_WB_Data),
      .reg_num(reg_num),
      .reg_data(reg_data),
      .reg_write_sig(reg_write_sig),
      .wr(wr),
      .rd(rd),
      .addr(addr),
      .wr_data(wr_data),
      .rd_data(rd_data)
  );

  initial begin
    if ($value$plusargs("vcd=%s", vcd_file)) begin
      $dumpfile(vcd_file);
      $dumpvars(0, tb_clk, reset, tb_WB_Data);
      $dumpvars(0, reg_num, reg_data, reg_write_sig, wr, rd, addr, wr_data, rd_data);
      $dumpvars(0, riscV.dp.PC, riscV.dp.Instr, riscV.dp.Next_PC, riscV.dp.PCPlus4);
      $dumpvars(0, riscV.dp.A, riscV.dp.B, riscV.dp.C, riscV.dp.D);
      $dumpvars(0, riscV.dp.Reg_Stall, riscV.dp.PcSel, riscV.dp.ALUResult);
      $dumpvars(0, riscV.dp.FAmuxSel, riscV.dp.FBmuxSel, riscV.dp.SrcB);
      $dumpvars(0, riscV.opcode, riscV.Operation, riscV.Funct3, riscV.Funct7);
    end

    tb_clk = 0;
    reset  = 1;
    #(CLKPERIOD);
    reset = 0;

    #(CLKPERIOD * 50);

    $stop;
  end

  always_comb begin : MEMORY
    if (wr && ~rd)
      $display($time, ": Memory [%d] written with value: [%X] | [%d]\n", addr, wr_data, wr_data);

    else if (rd && ~wr)
      $display($time, ": Memory [%d] read with value: [%X] | [%d]\n", addr, rd_data, rd_data);
  end : MEMORY

  always_comb begin : REGISTER
    if (reg_write_sig)
      $display(
          $time, ": Register [%d] written with value: [%X] | [%d]\n", reg_num, reg_data, reg_data
      );
  end : REGISTER

  //clock generator
  always #(CLKDELAY) tb_clk = ~tb_clk;

endmodule
