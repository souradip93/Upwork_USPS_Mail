import math

#barcode-to-bit permutation
desc_char 	= [7,1,9,5,8,0,2,4,6,3,5,8,9,7,3,0,6,1,7,4,6,8,9,2,5,1,7,5,4,3,
8,7,6,0,2,5,4,9,3,0,1,6,8,2,0,4,5,9,6,7,5,2,6,3,8,5,1,9,8,7,4,0,2,6,3]
desc_bit 	= [4,1024,4096,32,512,2,32,16,8,512,2048,32,1024,2,64,8,16,2,
1024,1,4,2048,256,64,2,4096,8,256,64,16,16,2048,1,64,2,512,2048,32,8,128,8,
1024,128,2048,256,4,1024,8,32,256,1,8,4096,2048,256,16,32,2,8,1,128,4096,512,
256,1024]
asc_char 	= [4,0,2,6,3,5,1,9,8,7,1,2,0,6,4,8,2,9,5,3,0,1,3,7,4,6,8,9,2,0,5,
1,9,4,3,8,6,7,1,2,4,3,9,5,7,8,3,0,2,1,4,0,9,1,7,0,2,4,6,3,7,1,9,5,8]
asc_bit 	= [8,1,256,2048,2,4096,256,2048,1024,64,16,4096,4,128,512,64,128,
512,4,256,16,1,4096,128,1024,512,1,128,1024,32,128,512,64,256,4,4096,2,16,4,1,
2,32,16,64,4096,2,1,512,16,128,32,1024,4,64,512,2048,4,4096,64,128,32,2048,1,
8,4]

#build tables of 13-bit codewords
encode_table 	= [None] * 1365
decode_table 	= [None] * 8192
fcs_table 		= [None] * 8192

def build_codewords(bits, low, hi):
	#loop through all possible 13-bit codewords
	for fwd in range(8192):
		#build reversed codeword and count population of 1-bits
		pop = 0
		rev = 0
		tmp = fwd
		for bit in range(13):
			pop += tmp & 1
			rev = (rev << 1) | (tmp & 1)
			tmp >>= 1

		if pop != bits:
			continue

		if (fwd == rev):
			#palindromic codes go at the end of the table
			encode_table[hi] = fwd
			decode_table[fwd] = hi
			decode_table[fwd ^ 8191] = hi
			fcs_table[fwd] = 0
			fcs_table[fwd ^ 8191] = 1
			hi-=1

		elif (fwd < rev):
			#add foreward code to front of table
			encode_table[low] = fwd
			decode_table[fwd] = low
			decode_table[fwd ^ 8191] = low
			fcs_table[fwd] = 0
			fcs_table[fwd ^ 8191] = 1
			low+=1

			#add reversed code to front of table
			encode_table[low] = rev
			decode_table[rev] = low
			decode_table[rev ^ 8191] = low
			fcs_table[rev] = 0
			fcs_table[rev ^ 8191] = 1
			low+=1
    
  
build_codewords(5,    0, 1286)
build_codewords(2, 1287, 1364)

def add(num, add):
	# num is an array of 11-bit words representing a multiple-precision number.
	# add "add" to num.
	for n in range(len(num)-1,-1,-1):
		if add==0:
			return
		x = num[n] + add
		add = x >> 11
		num[n] = x & 0x7ff


def muladd(num, mult, add):
	# num is an array of 11-bit words representing a multiple-precision number.
	# multiply num by "mult" and add "add".
	# assuming 32-bit integers, the largest mult can be without overflowing
	# is about 2**20, approximately one million.
	for n in range(len(num)-1,-1,-1):
		x = num[n]*mult + add
		add = x >> 11
		num[n] = x & 0x7ff
 
def divmod(num, div):
	# num is an array of 11-bit words representing a multiple-precision number.
	# divide num by "div" and return remainder.
	# div is limited the same way as mult above.
	mod = 0
	leng = len(num)
	for n in range(leng):
		x = num[n] + (mod << 11)
		num[n] = q = math.floor(x / div)
		mod = x - q*div
  
	return mod


def iszero(num):
	# num is an array of 11-bit words representing a multiple-precision number.
	# see if num is zero.
	for n in range(len(num)-1,-1,-1):
		if (num[n] != 0):
			return False
	return True


def calcfcs(num):
  #calculate 11-bit frame check sequence for an array of 11-bit words.
	fcs = 0x1f0
	leng = len(num)
	for n in range(leng):
		fcs ^= num[n]
		for bit in range(11):
			fcs <<= 1
			if (fcs & 0x800): 
				fcs ^= 0xf35
    
	return fcs;

def clean_str(str):
	if (str == None):
		str = ''
  
	return str.upper().replace(' ', '')


def isdigits(str,n=0):
	if (not str.isdigit()):
		return False
	return not n or len(str) == n


def text_to_chars(barcode, strict):
	#convert barcode text to "characters" by applying bit permutation
	barcode = clean_str(barcode)
	chars = [0,0,0,0,0,0,0,0,0,0]
  
	for n in range(65):
		letter = barcode[n]
		if letter == 'T' or letter == 'S':  # track bar
			pass;
		elif letter == 'D':  # descending bar
			chars[desc_char[n]] |= desc_bit[n]
		elif letter == 'A':  # ascending bar
			chars[asc_char[n]] |= asc_bit[n]
		elif letter == 'F':  # full bar
			chars[desc_char[n]] |= desc_bit[n]
			chars[asc_char[n]] |= asc_bit[n]
		else:
			return None;
    
	return chars;


def chars_to_text(chars):
	barcode = ""
	for n in range(65):
		if (chars[desc_char[n]] & desc_bit[n]):
			if (chars[asc_char[n]] & asc_bit[n]):
				barcode += "F"
			else:
				barcode += "D"
		
		else:
			if (chars[asc_char[n]] & asc_bit[n]):
				barcode += "A"
			else:
				barcode += "T"
	return barcode;

def decode_chars(chars):
	#decode characters to codewords.
	#this is the core of the barcode processing.

	cw = [None]*10
	fcs = 0
  
	for n in range(10):
		cw[n] = decode_table[chars[n]]
		if (cw[n] == None):
			return None
		fcs |= fcs_table[chars[n]] << n

	# codewords valid?
	if (cw[0] > 1317 or cw[9] > 1270):
		return
	
	if (cw[9] & 1):
		# If the barcode is upside down, cw[9] will always be odd.
		# This is due to properties of the bit permutation and the
		# codeword table.
		return None
	
	cw[9] >>= 1
	if (cw[0] > 658):
		cw[0] -= 659
		fcs |= 1 << 10
	

	# convert codewords to binary
	num = [0,0,0,0,0,0,0,0,0,cw[0]]
	for n in range(1,9):
		muladd(num, 1365, cw[n])
		
	muladd(num, 636, cw[9])

	if (calcfcs(num) != fcs): 
		return None

	# decode tracking information
	track = [None]*20
	for n in range(19,1,-1):
		track[n] = divmod(num, 10)
	
	track[1] = divmod(num, 5)
	track[0] = divmod(num, 10)

	# decode routing information (zip code, etc)
	route = [None]*11
	pos = 11;
	
	for sz in range(5,1,-1):
		if (sz == 3):
			continue
		if (iszero(num)): 
			break
		add(num, -1)
		for n in range(sz):
			pos-=1
			route[pos] = divmod(num, 10)
	
	if (sz < 2 and not iszero(num)):
		return None;

	# finally finished decoding
	track = [str(x) for x in track]
	route = [str(x) for x in route]
	
	inf = {}
	inf['barcode_id'] = ''.join(track[0:2])
	inf['service_type'] = ''.join(track[2:5])
	if (track[5] == 9):
		inf['mailer_id'] = ''.join(track[5:14])
		inf['serial_num'] = ''.join(track[14:20])
	
	else:
		inf['mailer_id'] = ''.join(track[5:11])
		inf['serial_num'] = ''.join(track[11:20])
	
	if (pos <= 6):
		inf['zip'] = ''.join(route[pos:pos+5])
	if (pos <= 2):
		inf['plus4'] = ''.join(route[pos+5:pos+9])
	if (pos == 0):
		inf['delivery_pt'] = ''.join(route[9:11])
	return inf;


def try_repair(possible, chars, pos):
	p = possible[pos]
	inf = None
	leng = len(p)
	for n in range(leng):
		chars[pos] = p[n]
		if (pos < 9):
			newinf = try_repair(possible, chars, pos+1)
		else:
			newinf = decode_chars(chars)
			if(newinf):
				newinf['suggest'] = chars_to_text(chars)
				newinf['message'] = "Damaged barcode"
		
	if (newinf):
		# abort if multiple solutions are found.
		if (inf): 
			return { message: "Invalid barcode" }
		inf = newinf

	return inf;

def repair_chars(chars):
	possible = [None]*10
	prod = 1
	for n in range(10):
		possible[n] = []
		c = chars[n]
		if (decode_table[c] == None):
			for bit in range(13):
				d = c ^ (1 << bit)
				if (decode_table[d] != None):
					possible[n].append(d)
		  
		
		else:
		  possible[n].append(c)
		
		# Don't let the number of possible combinations get too high --
		# it will take too long to run, and it won't find a unique
		# solution anyway.
		prod *= len(possible[n]);
		if (prod == 0 or prod > 1000):
			return None;
	  
	newchars = [None]*10
	return try_repair(possible, newchars, 0)


def flip_barcode(barcode):
	flipped = ""
	for n in range(len(barcode) - 1, -1, -1):
		c = barcode[n]
		if (c == "A"):
		  flipped += "D"
		elif (c == "D"):
		  flipped += "A"
		else:
		  flipped += c
	  
	return flipped

def repair_barcode(barcode):
	
	if (len(barcode) == 64):
		longer = True
	elif (len(barcode) == 66):
		longer = False
	else:
		return barcode

	best = barcode
	besterrs = 5  # don't try to repair if we can't get more than 5 right

	for pos in range(66):
		if (longer):
			testcode = barcode[0:pos] + "X" + barcode[pos:]
		else:
			testcode = barcode[0:pos] + barcode[pos+1:]
		chars = text_to_chars(testcode, False)
		errs = 0
		for n in range(10):
			if (decode_table[chars[n]] == None):
				errs+=1
		if (errs < besterrs):
			besterrs = errs
			best = testcode
	

	return best;


def find_diffs(str1, str2):
	leng = min([len(str1), len(str2)])
	diffs = [None]*leng
	  
	for n in range(leng):
		diffs[n] = str1[n] != str2[n]
	return diffs



def check_fields(inf):
	for field in inf:
		inf[field] = clean_str(inf[field])

	if (inf['zip'] != ""):
		if (not isdigits(inf['zip'],5)):
			return "Zip code must be 5 digits"
  
	if (inf['plus4'] != ""):
		if (inf['zip'] == ""):
			return "Zip code required";
		if (not isdigits(inf['plus4'],4)):
			return "Zip+4 must be 4 digits"
	
	if (inf['delivery_pt'] != ""):
		if (inf['plus4'] == ""):
			return "Zip+4 required"
		if (not isdigits(inf['delivery_pt'],2)):
			return "Delivery Point must be 2 digits"
	

	if (not isdigits(inf['barcode_id'],2)):
		return "Barcode ID must be 2 digits"
	if (inf['barcode_id'][1] >= "5"):
		return "Second digit of Barcode ID must be 0-4"
	if (not isdigits(inf['service_type'],3)):
		return "Service Type must be 3 digits"
	if (not isdigits(inf['mailer_id']) or len(inf['mailer_id']) != 6 and len(inf['mailer_id']) != 9):
		return "Mailer ID must be 6 or 9 digits"
	if (not isdigits(inf['serial_num']) or len(inf['mailer_id']) + len(inf['serial_num']) != 15):
		return "Mailer ID and Serial Number together must be 15 digits"

	return None;


def encode_fields(inf):
	num = [0,0,0,0,0,0,0,0,0,0]
	marker = 0
	if (inf['zip'] != ""):
		num[9] = int(inf['zip'])
		marker += 1
  
	if (inf['plus4'] != ""):
		muladd(num, 10000, int(inf['plus4']))
		marker += 100000
  
	if (inf['delivery_pt'] != ""):
		muladd(num, 100, int(inf['delivery_pt']))
		marker += 1000000000
  
	add(num, marker)

	muladd(num, 10, int(inf['barcode_id'][0]))
	muladd(num, 5, int(inf['barcode_id'][1]))
	muladd(num, 1000, int(inf['service_type']))
  
	if len(inf['mailer_id']) == 6:
		muladd(num, 1000000, int(inf['mailer_id']))
		muladd(num, 100000, 0)  # multiply in two steps to avoid overflow
		muladd(num, 10000, int(inf['serial_num']))
  
	else:
		muladd(num, 10000, 0)
		muladd(num, 100000, int(inf['mailer_id']))
		muladd(num, 1000000, int(inf['serial_num']))

	fcs = calcfcs(num)

	cw = [None] * 10
	cw[9] = divmod(num, 636) << 1
  
	for n in range(8,0,-1):
		cw[n] = divmod(num, 1365)
		
	cw[0] = (num[8]<<11) | num[9]
	
	if (fcs & (1 << 10)):
		cw[0] += 659;

	chars = [None]*10
	for n in range(10):
		chars[n] = encode_table[cw[n]]
		if (fcs & (1 << n)):
			chars[n] ^= 8191
  

	return chars_to_text(chars)


barcode_fields = [ "zip", "plus4", "delivery_pt", "barcode_id",
   "service_type", "mailer_id", "serial_num" ]

def do_decode():

	encode_form = {}
	for i in range(len(barcode_fields)):
		encode_form[barcode_fields[i]] = "";

	#var decode_form = document.forms.decode_form;
	decode_form_barcode_value = input("Enter barcode : ")
	inf = decode_barcode(decode_form_barcode_value);

	msg = "";
	if ("message" in inf.keys()):
		msg = inf['message']
	if ("suggest"  in inf.keys()):
		if (msg): 
			msg += " "
		msg += "Suggest replacement: "
		if ("highlight" in inf.keys()):
			msg += highlight(inf['suggest'], inf['highlight'])
		else:
			msg += inf['suggest']
	
	print(msg)

	for i in range(len(barcode_fields)):
		if (barcode_fields[i] in inf.keys()):
			encode_form[barcode_fields[i]] = inf[barcode_fields[i]];
	
	print(encode_form)
	# lookup = get_zip_url(inf)
	# if (lookup):
		# document.getElementById('zip_lookup').innerHTML =
		# '<a target="_blank" href="' + lookup + '">Lookup</a>';
	
	# else:
		# document.getElementById('zip_lookup').innerHTML = '';

		
def decode_barcode(barcode):

	barcode = clean_str(barcode)
	if (len(barcode) == 65):
		chars = text_to_chars(barcode, True)
		if (chars):
			inf = decode_chars(chars)
			if (inf):
				return inf  # decoded with no errors
		

	barcode = repair_barcode(barcode)
	if (len(barcode) != 65):
		return { 'message': "Barcode must be 65 characters long" }

	chars = text_to_chars(barcode, False)
	inf = repair_chars(chars)
	if (inf):
		if (inf['suggest']):
			inf['highlight'] = find_diffs(barcode, inf['suggest']);
		return inf

	barcode = flip_barcode(barcode)
	chars = text_to_chars(barcode, False)
	inf = repair_chars(chars)
	if (inf and inf['barcode_id']):
		inf['message'] = "Barcode seems to be upside down"
		return inf

	return { 'message': "Invalid barcode" }

def do_encode():

	encode_form = {};
	
	for i in range(len(barcode_fields)):
		encode_form[barcode_fields[i]] = input("Enter "+barcode_fields[i]+" : ")
	
	inf = {}
	for i in range(len(barcode_fields)):
		inf[barcode_fields[i]] = encode_form[barcode_fields[i]]

	message = check_fields(inf)
	if (message):
		print(message)
		return
	else:
		decode_form_barcode_value = encode_fields(inf)
		#show_barcode();
	
	print(decode_form_barcode_value)


def do_update():
	leng = show_barcode()
	if (leng == 65): do_decode()

	
do_encode()
