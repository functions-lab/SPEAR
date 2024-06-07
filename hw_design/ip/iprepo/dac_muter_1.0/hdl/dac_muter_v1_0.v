
`timescale 1 ns / 1 ps

module dac_muter_v1_0 #(

    // Parameters of AXI Stream Master/Slave Bus Interface S_AXIS
    parameter integer C_AXIS_TDATA_WIDTH = 32
) (

    // Ports of Axi Slave Bus Interface S_AXIS
    input wire s_axis_aclk,
    input wire s_axis_aresetn,
    output reg s_axis_tready,
    input wire [C_AXIS_TDATA_WIDTH-1 : 0] s_axis_tdata,
    input wire s_axis_tvalid,

    // Ports of Axi Master Bus Interface M_AXIS
    input wire m_axis_aclk,
    input wire m_axis_aresetn,
    output reg m_axis_tvalid,
    output reg [C_AXIS_TDATA_WIDTH-1 : 0] m_axis_tdata,
    input wire m_axis_tready
);

  always @(*) begin  // tdata
    if (s_axis_tvalid && m_axis_tready) begin
      m_axis_tdata = s_axis_tdata;
    end else begin
      m_axis_tdata = {{C_AXIS_TDATA_WIDTH} {1'b0}};
    end
  end

  always @(*) begin  // tready tvalid
    s_axis_tready = m_axis_tready;
    m_axis_tvalid = s_axis_tvalid;
  end

endmodule