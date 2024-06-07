
`timescale 1 ns / 1 ps

module adc_packet_generator_v1_0 #(
    // Users to add parameters here

    // User parameters ends
    // Do not modify the parameters beyond this line

    // Parameters of Axi Slave Bus Interface S_AXI
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 4,

    // Parameters of Axi Stream  Master/Slave Bus Interface S_AXIS/M_AXIS
    parameter integer C_AXIS_TDATA_WIDTH = 32
) (
    // Users to add ports here

    output wire [C_S_AXI_DATA_WIDTH-1:0] axis_hs_counter,

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

    // Ports of Axi Slave Bus Interface S_AXIS
    input wire s_axis_aclk,
    input wire s_axis_aresetn,
    output wire s_axis_tready,
    input wire [C_AXIS_TDATA_WIDTH-1 : 0] s_axis_tdata,
    input wire s_axis_tvalid,

    // Ports of Axi Master Bus Interface M_AXIS
    input wire m_axis_aclk,
    input wire m_axis_aresetn,
    output wire m_axis_tvalid,
    output wire [C_AXIS_TDATA_WIDTH-1 : 0] m_axis_tdata,
    output wire m_axis_tlast,
    input wire m_axis_tready
);
  // Instantiation of Axi Bus Interface S_AXI
  adc_packet_generator_v1_0_S_AXI #(
      .C_S_AXI_DATA_WIDTH(C_S_AXI_DATA_WIDTH),
      .C_S_AXI_ADDR_WIDTH(C_S_AXI_ADDR_WIDTH)
  ) adc_packet_generator_v1_0_S_AXI_inst (

      .enable_o(enable_o),
      .packet_size_o(packet_size_o),
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

  // Add user logic here

  // Connecting M_AXIS and S_AXIS
  assign s_axis_tready = m_axis_tready;
  assign m_axis_tdata  = s_axis_tdata;
  assign m_axis_tvalid = s_axis_tvalid;

  wire [C_S_AXI_DATA_WIDTH-1:0] enable, enable_o, curr_state_i, packet_size_o;
  wire [C_S_AXI_DATA_WIDTH-1:0] enable_r, packet_size_r;
  reg [C_S_AXI_DATA_WIDTH-1:0] axis_hs_counter_r;

  reg [1:0] curr_state, next_state;
  wire axis_hs;

  ffd_synchro #(
      .DATA_WIDTH(C_S_AXI_DATA_WIDTH)
  ) enable_s (
      .aclk(s_axis_aclk),
      .aresetn(s_axis_aresetn),
      .data_i(enable_o),
      .data_o(enable_r)
  );
  ffd_synchro #(
      .DATA_WIDTH(C_S_AXI_DATA_WIDTH)
  ) packet_size_s (
      .aclk(s_axis_aclk),
      .aresetn(s_axis_aresetn),
      .data_i(packet_size_o),
      .data_o(packet_size_r)
  );

  localparam S_IDLE = 2'b00, S_INCR = 2'b01, S_TLAST = 2'b10;

  assign axis_hs = s_axis_tready & s_axis_tvalid;
  assign enable = enable_r[0];
  assign curr_state_i = {{C_S_AXI_DATA_WIDTH - 2{1'b0}}, curr_state};

  always @(posedge s_axis_aclk, negedge s_axis_aresetn) begin
    if (!s_axis_aresetn) curr_state <= S_IDLE;
    else curr_state <= next_state;
  end  // State Register

  always @(posedge s_axis_aclk, negedge s_axis_aresetn) begin
    if (!s_axis_aresetn) axis_hs_counter_r <= {C_S_AXI_DATA_WIDTH{1'b0}};
    else begin
      if (curr_state == S_IDLE || curr_state == S_TLAST)
        axis_hs_counter_r <= {C_S_AXI_DATA_WIDTH{1'b0}};
      else if ((curr_state == S_INCR) && axis_hs) axis_hs_counter_r <= axis_hs_counter_r + 1;
    end
  end  // axis_hs_counter_r

  ffd_synchro #(
      .DATA_WIDTH(C_S_AXI_DATA_WIDTH)
  ) axis_hs_counter_s (
      .aclk(s_axi_aclk),
      .aresetn(s_axi_aresetn),
      .data_i(axis_hs_counter_r),
      .data_o(axis_hs_counter)
  ); // axis_hs_counter

  always @(*) begin
    next_state = S_IDLE;

    case (curr_state)
      S_IDLE: begin
        if (enable) next_state = S_INCR;
        else next_state = S_IDLE;
      end
      S_INCR: begin
        if (axis_hs_counter_r >= (packet_size_r - 1)) next_state = S_TLAST;
        else next_state = S_INCR;
      end
      S_TLAST: begin
        if (axis_hs) begin
          if (enable) next_state = S_INCR;
          else next_state = S_IDLE;
        end else begin
          next_state = S_TLAST;
        end
      end
      default: begin
        next_state = S_IDLE;
      end
    endcase
  end  // Next State Logic (C)

  assign m_axis_tlast = (curr_state == S_TLAST) && axis_hs;

  // User logic ends

endmodule














