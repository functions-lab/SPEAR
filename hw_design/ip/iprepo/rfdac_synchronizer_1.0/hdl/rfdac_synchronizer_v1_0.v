
`timescale 1 ns / 1 ps

module rfdac_synchronizer_v1_0 #(
    // Users to add parameters here

    // User parameters ends
    // Do not modify the parameters beyond this line

    // Parameters of AXI Slave Bus Interface S_AXI
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 4,

    // Parameters of AXI Stream Master/Slave Bus Interface AXIS
    parameter integer C_AXIS_TDATA_WIDTH = 32
) (
    // Users to add ports here

    // User ports ends
    // Do not modify the ports beyond this line


    // Ports of Axi Slave Bus Interface S_AXI
    input wire s_axi_aclk,
    input wire s_axi_aresetn,
    input wire [C_S_AXI_ADDR_WIDTH-1 : 0] s_axi_awaddr,
    input wire [2 : 0] s_axi_awprot,
    input wire s_axi_awvalid,
    output wire s_axi_awready,
    input wire [C_S_AXI_DATA_WIDTH-1 : 0] s_axi_wdata,
    input wire [(C_S_AXI_DATA_WIDTH/8)-1 : 0] s_axi_wstrb,
    input wire s_axi_wvalid,
    output wire s_axi_wready,
    output wire [1 : 0] s_axi_bresp,
    output wire s_axi_bvalid,
    input wire s_axi_bready,
    input wire [C_S_AXI_ADDR_WIDTH-1 : 0] s_axi_araddr,
    input wire [2 : 0] s_axi_arprot,
    input wire s_axi_arvalid,
    output wire s_axi_arready,
    output wire [C_S_AXI_DATA_WIDTH-1 : 0] s_axi_rdata,
    output wire [1 : 0] s_axi_rresp,
    output wire s_axi_rvalid,
    input wire s_axi_rready,

    // Ports of Axi Slave Bus Interface S_AXIS_0
    input wire s_axis_0_aclk,
    input wire s_axis_0_aresetn,
    output wire s_axis_0_tready,
    input wire [C_AXIS_TDATA_WIDTH-1 : 0] s_axis_0_tdata,
    input wire s_axis_0_tlast,
    input wire s_axis_0_tvalid,

    // Ports of Axi Slave Bus Interface S_AXIS_1
    input wire s_axis_1_aclk,
    input wire s_axis_1_aresetn,
    output wire s_axis_1_tready,
    input wire [C_AXIS_TDATA_WIDTH-1 : 0] s_axis_1_tdata,
    input wire s_axis_1_tlast,
    input wire s_axis_1_tvalid,

    // Ports of Axi Slave Bus Interface S_AXIS_2
    input wire s_axis_2_aclk,
    input wire s_axis_2_aresetn,
    output wire s_axis_2_tready,
    input wire [C_AXIS_TDATA_WIDTH-1 : 0] s_axis_2_tdata,
    input wire s_axis_2_tlast,
    input wire s_axis_2_tvalid,

    // Ports of Axi Slave Bus Interface S_AXIS_3
    input wire s_axis_3_aclk,
    input wire s_axis_3_aresetn,
    output wire s_axis_3_tready,
    input wire [C_AXIS_TDATA_WIDTH-1 : 0] s_axis_3_tdata,
    input wire s_axis_3_tlast,
    input wire s_axis_3_tvalid,

    // Ports of Axi Master Bus Interface M_AXIS_0
    input wire m_axis_0_aclk,
    input wire m_axis_0_aresetn,
    output wire m_axis_0_tvalid,
    output wire [C_AXIS_TDATA_WIDTH-1 : 0] m_axis_0_tdata,
    output wire m_axis_0_tlast,
    input wire m_axis_0_tready,

    // Ports of Axi Master Bus Interface M_AXIS_1
    input wire m_axis_1_aclk,
    input wire m_axis_1_aresetn,
    output wire m_axis_1_tvalid,
    output wire [C_AXIS_TDATA_WIDTH-1 : 0] m_axis_1_tdata,
    output wire m_axis_1_tlast,
    input wire m_axis_1_tready,

    // Ports of Axi Master Bus Interface M_AXIS_2
    input wire m_axis_2_aclk,
    input wire m_axis_2_aresetn,
    output wire m_axis_2_tvalid,
    output wire [C_AXIS_TDATA_WIDTH-1 : 0] m_axis_2_tdata,
    output wire m_axis_2_tlast,
    input wire m_axis_2_tready,

    // Ports of Axi Master Bus Interface M_AXIS_3
    input wire m_axis_3_aclk,
    input wire m_axis_3_aresetn,
    output wire m_axis_3_tvalid,
    output wire [C_AXIS_TDATA_WIDTH-1 : 0] m_axis_3_tdata,
    output wire m_axis_3_tlast,
    input wire m_axis_3_tready
);
  // Instantiation of Axi Bus Interface S_AXI
  rfdac_synchronizer_v1_0_S_AXI #(
      .C_S_AXI_DATA_WIDTH(C_S_AXI_DATA_WIDTH),
      .C_S_AXI_ADDR_WIDTH(C_S_AXI_ADDR_WIDTH)
  ) rfdac_synchronizer_v1_0_S_AXI_inst (
      .S_AXI_ACLK(s_axi_aclk),
      .S_AXI_ARESETN(s_axi_aresetn),
      .S_AXI_AWADDR(s_axi_awaddr),
      .S_AXI_AWPROT(s_axi_awprot),
      .S_AXI_AWVALID(s_axi_awvalid),
      .S_AXI_AWREADY(s_axi_awready),
      .S_AXI_WDATA(s_axi_wdata),
      .S_AXI_WSTRB(s_axi_wstrb),
      .S_AXI_WVALID(s_axi_wvalid),
      .S_AXI_WREADY(s_axi_wready),
      .S_AXI_BRESP(s_axi_bresp),
      .S_AXI_BVALID(s_axi_bvalid),
      .S_AXI_BREADY(s_axi_bready),
      .S_AXI_ARADDR(s_axi_araddr),
      .S_AXI_ARPROT(s_axi_arprot),
      .S_AXI_ARVALID(s_axi_arvalid),
      .S_AXI_ARREADY(s_axi_arready),
      .S_AXI_RDATA(s_axi_rdata),
      .S_AXI_RRESP(s_axi_rresp),
      .S_AXI_RVALID(s_axi_rvalid),
      .S_AXI_RREADY(s_axi_rready),
      .slv_reg0(enable_r),
      .slv_reg1(reg1_r),
      .slv_reg2(reg2_r),
      .slv_reg3(reg3_r)
  );

  // Add user logic here
  reg [C_S_AXI_DATA_WIDTH-1:0] enable_r;
  reg [C_S_AXI_DATA_WIDTH-1:0] reg1_r;
  reg [C_S_AXI_DATA_WIDTH-1:0] reg2_r;
  reg [C_S_AXI_DATA_WIDTH-1:0] reg3_r;

  wire m_axis_all_ready, s_axis_all_valid;

  // Connect S_AXIS_0 to M_AXIS_0
  assign m_axis_0_tdata = s_axis_0_tdata;
  assign m_axis_0_tlast = s_axis_0_tlast;

  // Connect S_AXIS_1 to M_AXIS_1
  assign m_axis_1_tdata = s_axis_1_tdata;
  assign m_axis_1_tlast = s_axis_1_tlast;

  // Connect S_AXIS_2 to M_AXIS_2
  assign m_axis_2_tdata = s_axis_2_tdata;
  assign m_axis_2_tlast = s_axis_2_tlast;

  // Connect S_AXIS_3 to M_AXIS_3
  assign m_axis_3_tdata = s_axis_3_tdata;
  assign m_axis_3_tlast = s_axis_3_tlast;

  // TVALID
  assign s_axis_all_valid = s_axis_0_tvalid & s_axis_1_tvalid & s_axis_2_tvalid & s_axis_3_tvalid & enable_r;
  assign {m_axis_0_tvalid, m_axis_1_tvalid, m_axis_2_tvalid, m_axis_3_tvalid} = {4{s_axis_all_valid}};

  // TREADY
  assign m_axis_all_ready = m_axis_0_tready & m_axis_1_tready & m_axis_2_tready & m_axis_3_tready & enable_r;
  assign {s_axis_0_tready, s_axis_1_tready, s_axis_2_tready,s_axis_3_tready} = {4{m_axis_all_ready}};

  // User logic ends

endmodule