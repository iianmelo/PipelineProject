// Behavioral stand-in for the Intel FPGA altsyncram megafunction.
//
// Covers only the dual-port, 8-bit, MIF-initialized configuration instantiated
// by design/ramOnChip32.v and design/ramOnChipData.v:
//   * write port A, read port B
//   * read address registered on clock0 (ADDRESS_REG_B = "CLOCK0")
//   * read data unregistered (OUTDATA_REG_B = "UNREGISTERED")
//   * power-up contents taken from init_file (Altera MIF, DATA_RADIX = BIN)
//
// ModelSim keeps using the vendor library (altera_mf_ver). This file is
// compiled only by the Icarus flow in sim/run_icarus.sh.

module altsyncram (
    address_a,
    address_b,
    clock0,
    data_a,
    wren_a,
    q_b,
    aclr0,
    aclr1,
    addressstall_a,
    addressstall_b,
    byteena_a,
    byteena_b,
    clock1,
    clocken0,
    clocken1,
    clocken2,
    clocken3,
    data_b,
    eccstatus,
    q_a,
    rden_a,
    rden_b,
    wren_b
);
  parameter width_a = 8;
  parameter width_b = 8;
  parameter numwords_a = 65536;
  parameter numwords_b = 65536;
  parameter widthad_a = 16;
  parameter widthad_b = 16;
  parameter width_byteena_a = 1;
  parameter init_file = "UNUSED";
  parameter address_reg_b = "CLOCK0";
  parameter outdata_reg_b = "UNREGISTERED";
  parameter operation_mode = "DUAL_PORT";
  parameter intended_device_family = "Cyclone IV GX";
  parameter lpm_type = "altsyncram";
  parameter address_aclr_b = "NONE";
  parameter clock_enable_input_a = "BYPASS";
  parameter clock_enable_input_b = "BYPASS";
  parameter clock_enable_output_b = "BYPASS";
  parameter outdata_aclr_b = "NONE";
  parameter power_up_uninitialized = "FALSE";
  parameter read_during_write_mode_mixed_ports = "DONT_CARE";

  input [widthad_a-1:0] address_a;
  input [widthad_b-1:0] address_b;
  input clock0;
  input [width_a-1:0] data_a;
  input wren_a;
  output [width_b-1:0] q_b;
  input aclr0;
  input aclr1;
  input addressstall_a;
  input addressstall_b;
  input byteena_a;
  input byteena_b;
  input clock1;
  input clocken0;
  input clocken1;
  input clocken2;
  input clocken3;
  input [width_b-1:0] data_b;
  output [2:0] eccstatus;
  output [width_a-1:0] q_a;
  input rden_a;
  input rden_b;
  input wren_b;

  localparam DEPTH = 65536;

  reg [width_a-1:0] mem[0:DEPTH-1];
  reg [widthad_b-1:0] raddr_q;

  integer fd, code, addr, value, i;

  reg [8*512-1:0] line;

  assign eccstatus = 3'b000;
  assign q_a = {width_a{1'b0}};
  assign q_b = mem[raddr_q];

  initial begin
    raddr_q = {widthad_b{1'b0}};
    for (i = 0; i < DEPTH; i = i + 1) mem[i] = {width_a{1'b0}};

    fd = $fopen(init_file, "r");
    if (fd == 0) begin
      $display("altsyncram: init file '%0s' not found; memory stays zero", init_file);
    end else begin
      while (!$feof(fd)) begin
        code  = $fgets(line, fd);
        addr  = -1;
        value = -1;
        code  = $sscanf(line, "%d: %b;", addr, value);
        if (code == 2) begin
          if (addr >= 0 && addr < DEPTH) mem[addr] = value[width_a-1:0];
        end
      end
      $fclose(fd);
    end
  end

  // Vendor RAM registers the read address on clock0 and presents the byte
  // combinationally afterwards. Writes are committed on the same clock.
  always @(posedge clock0) begin
    if (!addressstall_b) raddr_q <= address_b;
    if (wren_a) mem[address_a] <= data_a;
  end

endmodule
