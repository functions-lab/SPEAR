`timescale 1 ns / 1 ps

module ffd_synchro #(
    parameter integer DATA_WIDTH = 32
) (
    input wire aclk,
    input wire aresetn,
    input wire [DATA_WIDTH-1:0] data_i,
    output wire [DATA_WIDTH-1:0] data_o
);

  reg [DATA_WIDTH-1:0] sync_1, sync_2;

  always @(posedge aclk or negedge aresetn) begin

    if (!aresetn) begin
      sync_1 <= {{DATA_WIDTH} {1'b0}};
      sync_2 <= {{DATA_WIDTH} {1'b0}};
    end else begin
      sync_1 <= data_i;
      sync_2 <= sync_1;
    end
  end

  assign data_o = sync_2;

endmodule



