
import json

o_json = json.loads( open( "characters.json" ).read() )

#print json.dumps( sorted( o_json.keys() ), indent=2 )


FRIENDS_EP_1 = [
  "Jones Family", 
  "Non-Family Survivors", 
  "Andrea's Family", 
  "Carol's Family", 
  "Greene Family", 
  "Greene Neighbors", 
]

c = 0
for f in FRIENDS_EP_1:
    #c += len( o_json[ f ] )
    c += str( o_json[ f ] ).count( "Alive" )
print c
