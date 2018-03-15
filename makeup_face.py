from visage import ApplyMakeup
from visage import DetectLandmarks
AM = ApplyMakeup()
output_file = AM.apply_lipstick('/Users/forzfilm/Desktop/Flexmedia/sticker/kissitbetter.jpg',170,10,30,"upper") # (R,G,B) - (170,10,30)
output_file = AM.apply_lipstick('/Users/forzfilm/Desktop/Flexmedia/sticker/output_lips_kissitbetter.jpg',119, 68, 140,"bottom") # (R,G,B) - (170,10,30)
output_file = AM.apply_lipstick('/Users/forzfilm/Desktop/Flexmedia/sticker/maxresdefault.jpg',170,10,30,"upper") # (R,G,B) - (170,10,30)
output_file = AM.apply_lipstick('/Users/forzfilm/Desktop/Flexmedia/sticker/output_lips_maxresdefault.jpg',119, 68, 140,"bottom") # (R,G,B) - (170,10,30)
