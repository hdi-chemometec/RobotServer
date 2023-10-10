from opentrons import protocol_api

#metadata
metadata = {'apiLevel': '2.0'}

requirements = {"robotType": "OT-2", "apiLevel": "2.0"}

#protocol run function
def run(protocol: protocol_api.ProtocolContext):
    #pipettes
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', location='1')
    right_pipette = protocol.load_instrument('p300_single', mount='right', tip_racks=[tiprack])

    #commands
    try:
        right_pipette.pick_up_tip()
    except protocol_api.labware.OutOfTipsError:
        protocol.pause("The pipette is out of tips")
    protocol.pause("The pipette is ready to drop the tip")
    right_pipette.drop_tip()