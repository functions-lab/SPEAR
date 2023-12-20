

class TxChannel:
    def __init__(self, dma, gain, sample_rate, tile, block):
        # Basic info
        self.dac_tile_id = tile
        self.dac_id = block
        self.dac_tile_status
        # DAC status

        # 
        self.dma = dma
        self.gain = gain
        self.sample_rate = sample_rate
        self.tile = tile
        self.block = block
