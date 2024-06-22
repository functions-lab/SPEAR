
`timescale 1 ns / 1 ps

module data_mover_ctrl_v1_0 #(
    // Users to add parameters here

    // User parameters ends
    // Do not modify the parameters beyond this line


    // Parameters of Axi Slave Bus Interface S_AXI
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 5,

    // Parameters of Axi Master Bus Interface M_AXIS
    parameter integer C_M_AXIS_TDATA_WIDTH = 104
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

    // Ports of Axi Master Bus Interface M_AXIS
    input wire m_axis_aclk,
    input wire m_axis_aresetn,
    output reg m_axis_tvalid,
    output reg [C_M_AXIS_TDATA_WIDTH-1 : 0] m_axis_tdata,
    input wire m_axis_tready
);

  wire start;
  wire [C_S_AXI_DATA_WIDTH-1:0] start_o;
  wire [C_S_AXI_DATA_WIDTH-1:0] curr_state_i, base_addr_upper_o, base_addr_lower_o, byte_to_transfer_o;
  reg [1:0] curr_state, next_state;

  // Instantiation of Axi Bus Interface S_AXI
  data_mover_ctrl_v1_0_S_AXI #(
      .C_S_AXI_DATA_WIDTH(C_S_AXI_DATA_WIDTH),
      .C_S_AXI_ADDR_WIDTH(C_S_AXI_ADDR_WIDTH)
  ) data_mover_ctrl_v1_0_S_AXI_inst (

      .start_o(start_o),
      .base_addr_upper_o(base_addr_upper_o),
      .base_addr_lower_o(base_addr_lower_o),
      .byte_to_transfer_o(byte_to_transfer_o),
      .curr_state_i(curr_state_i),

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
      .S_AXI_RREADY(s_axi_rready)
  );

  localparam S_IDLE = 2'b00, S_STREAM = 2'b01, S_ERROR = 2'b10;
  assign curr_state_i = {{C_S_AXI_DATA_WIDTH - 2{1'b0}}, curr_state};

  always @(posedge m_axis_aclk, negedge m_axis_aresetn) begin
    if (!m_axis_aresetn) curr_state <= S_IDLE;
    else curr_state <= next_state;
  end  // State

  assign start = start_o[0];

  always @(*) begin
    next_state = S_IDLE;

    case (curr_state)
      S_IDLE: begin
        if (start) next_state = S_STREAM;
        else next_state = S_IDLE;
      end
      S_STREAM: begin
        if (!start) next_state = S_IDLE;
        else next_state = S_STREAM;
      end
      S_ERROR: begin
        next_state = S_IDLE;
      end
      default: begin
        next_state = S_IDLE;
      end
    endcase
  end  // Next State Logic (C)

  always @(*) begin
    m_axis_tdata  = {C_M_AXIS_TDATA_WIDTH{1'b0}};
    m_axis_tvalid = 1'b0;

    if (curr_state == S_STREAM) begin
      m_axis_tdata = {
        8'h00,
        base_addr_upper_o,
        base_addr_lower_o  /*base addr*/,
        8'h00,
        1'b1  /*For Type INCR*/,
        byte_to_transfer_o[22:0]  /*BTT*/
      };
      m_axis_tvalid = m_axis_tready;
    end else begin
      m_axis_tdata  = {{C_M_AXIS_TDATA_WIDTH - 1{1'b0}}, 1'b1};  // BTT cannot be all zeros
      m_axis_tvalid = 1'b0;
    end
  end
  // User logic ends

endmodule