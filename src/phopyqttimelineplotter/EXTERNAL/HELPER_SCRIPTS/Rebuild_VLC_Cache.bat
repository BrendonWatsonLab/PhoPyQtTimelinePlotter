REM 
REM Run C:\Program Files\VideoLAN\VLC>vlc-cache-gen.exe "C:\Program Files\VideoLAN\VLC\plugins\"
REM fixes the VLC cache errors that appear in the terminal that result in slow video opening.
REM         See https://dev.getsol.us/T5893 for more info
REM         https://www.reddit.com/r/VLC/comments/9y63by/fix_slow_starting_vlc_30x_on_windows_10_by/

cd "C:\Program Files\VideoLAN\VLC\"
vlc-cache-gen.exe "C:\Program Files\VideoLAN\VLC\plugins\"
%pause
