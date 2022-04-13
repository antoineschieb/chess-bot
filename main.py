import winsound
import sys
import time
import numpy as np
import cv2
import wexpect
from win32gui import GetWindowText, GetForegroundWindow
import os.path
import datetime



 

from utils import standard_notation, str_of_casting_rights, screenshot, get_piece_code, correlate, simplify_line_str, trouver_coords, wrapper_imshow
from focus import WindowMgr



def generate_fen_from_cropped_im(im,color_to_play = 'w'):
    castling_rights =[]
    # 1 - remplir pièces echiquier
    fen = ''
    rows_list = []
    
    ww = min(int(im.shape[0]/8),int(im.shape[1]/8))
    for row in range(8):
        virtual_line = ''
        for col in range(8):
            square = im[ ww*row:ww*(row+1) , ww*col:ww*(col+1)]
            
            squareRGB = cv2.cvtColor(im,cv2.COLOR_GRAY2RGB)
            squareRGB[ww*row:ww*(row+1) , ww*col:ww*(col+1)] = (255,0,0)
            wrapper_imshow(squareRGB,square,aff=False,title='b')
            letter = get_piece_code(square)
            virtual_line += letter

        if row==0:
            if virtual_line[0]=='r' and virtual_line[4]=='k': #black can queenside castle 
                castling_rights.append('q')
            if virtual_line[-1]=='r' and virtual_line[4]=='k': #black can kingside castle 
                castling_rights.append('k')
        if row==7:
            if virtual_line[0]=='R' and virtual_line[4]=='K': #white can queenside castle 
                castling_rights.append('Q')
            if virtual_line[-1]=='R' and virtual_line[4]=='K': #white can kingside castle 
                castling_rights.append('K')
        
        rows_list.append(virtual_line)
        virtual_line = simplify_line_str(virtual_line)
        fen += virtual_line
        fen += '/'
    fen = fen[:-1]
    fen += ' '
    # 2 - Add 'w' or 'b'
    fen += color_to_play
    fen += ' '
    # 3 - Add castling rights
    fen += str_of_casting_rights(castling_rights)
    fen += ' '
    # 4 - Add en passant
    fen += '-'
    fen += ' '
    # 5 - Add nb moves since last capt + ' ' + moves since game started (blc pr l'instant)
    fen += '0 14'
    return fen,rows_list


def take_screenshot_and_crop_it(window_name='Live Chess - Chess.com - Google Chrome'):

    im = screenshot(window_name)
    if im:
        im = np.array(im)
        

        [x1,x2,y1,y2] = trouver_coords(im)
        
        return cv2.cvtColor(im[x1:x2,y1:y2],cv2.COLOR_BGR2GRAY) #giga important (zoom 110% si jamais) [haut,bas,gauche,droite]
    else:
        raise Exception("Pas pu prendre le screenshot !!")

def use_loaded_screenshot_and_crop_it():
    im = cv2.imread("./fixed.png")
    im = cv2.cvtColor(im,cv2.COLOR_RGB2GRAY)
    im = im[145:953,282:1090] #giga important (zoom 110% si jamais) [haut,bas,gauche,droite]
    return im


if __name__ == '__main__':
    oue = True
    nb_moves=0
    txt_window_current = GetWindowText(GetForegroundWindow())
    print(GetWindowText(GetForegroundWindow()))

    w_cmd = WindowMgr()
    w_cmd.find_window_wildcard(".*cmd.exe")
    #w_cmd.find_window_wildcard(txt_window_current)

    w_chr = WindowMgr()
    w_chr.find_window_wildcard(".*Chrome.*")

    save_path = 'M:/projets_perso/backseat_bot/log_files/'
    name_of_file = "log_"+str(int(time.time()))
    completeName = os.path.join(save_path, name_of_file+".txt")         
    file = open(completeName, "w") 
    file.write("LOGS for STOCKFISH OUTPUT :\n") 
    file.close() 



    while oue:
        
        color_to_play = input('Find best move for? (w/b)  ')
        assert color_to_play in ['w','b']
        if color_to_play==exit:
            sys.exit()
        print('screenshot in 1.5 seconds...')
        
        winsound.Beep(1500,60)
        time.sleep(0.3)
        winsound.Beep(1500,60)
        w_chr.set_foreground()
        time.sleep(1)
        im = take_screenshot_and_crop_it('Live Chess - Chess.com - Google Chrome')
        #im = use_loaded_screenshot_and_crop_it()
        winsound.PlaySound("sound/sfx.wav",winsound.SND_FILENAME)

        
        
        fen,rows_list = generate_fen_from_cropped_im(im,color_to_play)



        try:
            w_cmd.set_foreground()
        except Exception:
            pass


        print(f'FEN trouvée depuis le screen : {fen}')
        
        child = wexpect.spawn('stockfish_20090216_x64_bmi2.exe')        
        child.expect('\n')
        child.sendline('isready')
        child.expect('readyok')
        child.sendline('position fen '+fen)
        time.sleep(0.4)
        child.sendline('go movetime 1500')
        

        child.expect('ponder ')

        stockfish_analysis = child.before
       

        the_move = stockfish_analysis.split("bestmove ")[-1][:-1]
        full_line = stockfish_analysis.split("pv ")[-1].split("bestmove ")[0]

        for_str = 'for white' if color_to_play=='w' else 'for black'

        print(f'Best move {for_str} : {the_move}')
        print(standard_notation(the_move,rows_list))

        print(f'full line : {full_line}')

        child.sendline('exit')

        # Logging
        now = datetime.datetime.now()
        timestr = str(now.hour)+':' + str(now.minute)+':' +str(now.second)+':'
        file = open(completeName, "a") 
        file.write("Time    :   fen   -----> the_move :\n") 
        file.write(timestr + "  :  " + fen + '   ----->   ' + the_move +':\n')
        file.write("full stockfish output :\n")
        file.write(stockfish_analysis + '\n\n\n\n')
        file.close() 



        nb_moves+=1



