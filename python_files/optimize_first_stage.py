############################################################################
######## This script will optimize the first stage #########
############################################################################


#  Find IC_crit - obtain minimum gm whilst meeting noise spec (decreasing w which whilst keeping IC the same will increase noise)
#  Size the second stage Ciss to the biggest W that still meets the bandwidth 	<^-^>
#  determine the Id of the 2nd stage by setting the gm target. 			needs adjusting


# Read IC_crit and IC from the library: getpar("IC_CRIT_X1") and getpar("IC_X1")

# Scale W and I such that IC = IC_crit for best noise performance

# obtain noise transfer

# compare to noise specification

# scale w to just meet the noise spec, whilst keeping IC = IC_crit, thus also adjusting I

# if convergent, report the obtained W, I, IC and gm