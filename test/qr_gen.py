# pip install qrcode pillow matplotlib numpy
import qrcode, random
import numpy as np

def random_onbasis():
    e1 = np.array([1,0,0])
    e2 = np.array([0,1,0])
    e3 = np.array([0,0,1])
    
    u1 = np.array([random.randint(-255,255), random.randint(-255,255), random.randint(-255,255)])
    u1 = u1 / np.linalg.norm(u1)

    u2 = e2 - np.dot(e2, u1) / np.dot(u1, u1) * u1
    u2 = u2 / np.linalg.norm(u2)

    u3 = e3 - np.dot(e3, u1) / np.dot(u1, u1) * u1 - np.dot(e3, u2) / np.dot(u2, u2) * u2
    u3 = u3 / np.linalg.norm(u3)

    return [u1, u2, u3]

def onbasis(seed_vector):
    e1 = np.array([1,0,0])
    e2 = np.array([0,1,0])
    e3 = np.array([0,0,1])

    u1 = np.array(seed_vector)
    u1 = u1 / np.linalg.norm(u1)

    u2 = e2 - np.dot(e2, u1) / np.dot(u1, u1) * u1
    u2 = u2 / np.linalg.norm(u2)

    u3 = e3 - np.dot(e3, u1) / np.dot(u1, u1) * u1 - np.dot(e3, u2) / np.dot(u2, u2) * u2
    u3 = u3 / np.linalg.norm(u3)

    return [u1, u2, u3]

def random_normalbasis(min_dist):

    u1 = np.array([random.randint(-255,255), random.randint(-255,255), random.randint(-255,255)])
    u1 = u1 / np.linalg.norm(u1)
    
    while True:
        u2 = np.array([random.randint(-255,255), random.randint(-255,255), random.randint(-255,255)])
        u2 = u2 / np.linalg.norm(u2)
        if np.linalg.norm(u1-u2) < min_dist:
            break

    while True:
        u3 = np.array([random.randint(-255,255), random.randint(-255,255), random.randint(-255,255)])
        u3 = u3 / np.linalg.norm(u3)
        if np.linalg.norm(u1-u3) < min_dist and np.linalg.norm(u2-u3) < min_dist:
            break

    return [u1, u2, u3]

def noise(amplitude):
    n1 = random.random() * amplitude
    n2 = random.random() * amplitude
    n3 = random.random() * amplitude
    return [n1, n2, n3]

def transform_vector(vector, onbasis):
    x1 = np.dot(vector, onbasis[0])
    x2 = np.dot(vector, onbasis[1])
    x3 = np.dot(vector, onbasis[2])
    return (x1, x2, x3)

def invtransform_vector(vector, onbasis):
    x1 = vector[0]*onbasis[0][0] + vector[1]*onbasis[1][0] + vector[2]*onbasis[2][0]
    x2 = vector[0]*onbasis[0][1] + vector[1]*onbasis[1][1] + vector[2]*onbasis[2][1]
    x3 = vector[0]*onbasis[0][2] + vector[1]*onbasis[1][2] + vector[2]*onbasis[2][2]
    return (x1, x2, x3)

def qr_gen(text):
    img = qrcode.make(text)
    img.save("original.png")
    return img

def qr_encrypt(img, enc):
    new_img = img.convert('RGB')

    if enc == "RED":
        for i in range(new_img.size[0]):
            for j in range(new_img.size[1]):
                r, g, b = new_img.getpixel((i, j))
                if (r, g, b) == (0, 0, 0):
                    new_img.putpixel((i,j), (255, 0, 0))
    elif enc == "RED_SHUFFLE":
        for i in range(new_img.size[0]):
            for j in range(new_img.size[1]):
                r, g, b = new_img.getpixel((i, j))
                ran_g = random.randint(0,255)
                ran_b = random.randint(0,255)
                if (r, g, b) == (0, 0, 0):
                    new_img.putpixel((i,j), (255, ran_g, ran_b))
                else:
                    ran_g = random.randint(0,255)
                    ran_b = random.randint(0,255)
                    new_img.putpixel((i,j), (0, ran_g, ran_b))
    elif enc == "RED_BSHUFFLE":
        for i in range(round(new_img.size[0]/10)):
            for j in range(round(new_img.size[1]/10)):
                r, g, b = new_img.getpixel((i*10, j*10))
                ran_g = random.randint(0,255)
                ran_b = random.randint(0,255)
                if (r, g, b) == (0, 0, 0):
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), (255, ran_g, ran_b))
                else:
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), (0, int(ran_g), int(ran_b)))
    elif enc == "GREEN_BSHUFFLE":
        for i in range(round(new_img.size[0]/10)):
            for j in range(round(new_img.size[1]/10)):
                r, g, b = new_img.getpixel((i*10, j*10))
                ran_r = random.randint(0,255)
                ran_b = random.randint(0,255)
                if (r, g, b) == (0, 0, 0):
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), (ran_r, 255, ran_b))
                else:
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), (int(ran_r), 0, int(ran_b)))
    elif enc == "BLUE_BSHUFFLE":
        for i in range(round(new_img.size[0]/10)):
            for j in range(round(new_img.size[1]/10)):
                r, g, b = new_img.getpixel((i*10, j*10))
                ran_r = random.randint(0,255)
                ran_g = random.randint(0,255)
                if (r, g, b) == (0, 0, 0):
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), (ran_r, ran_g, 255))
                else:
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), (int(ran_r), int(ran_g), 0))
    elif enc == "YELLOW_BSHUFFLE":
        norm = np.linalg.norm(np.array([1,1]))
        basis = [np.array([1,1,0])/norm, np.array([0,1,1])/norm, np.array([1,0,1])/norm]
        for i in range(round(new_img.size[0]/10)):
            for j in range(round(new_img.size[1]/10)):
                r, g, b = new_img.getpixel((i*10, j*10))
                if (r, g, b) == (0, 0, 0):
                    new_pixel = np.array(invtransform_vector((255, random.randint(0,255), random.randint(0,255)), (basis)))
                    new_pixel = new_pixel / np.max(new_pixel) * 255
                    new_pixel = new_pixel.astype(int)
                    
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), tuple(new_pixel))
                else:
                    new_pixel = np.array(invtransform_vector((0, random.randint(0,255), random.randint(0,255)), (basis)))
                    new_pixel = new_pixel / np.max(new_pixel) * 255
                    new_pixel = new_pixel.astype(int)
                    
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), tuple(new_pixel))
    elif enc == "RANDOMON_BSHUFFLE":    # uses o.n.basis
        norm = np.linalg.norm(np.array([1,1]))
        basis = random_onbasis()
        print(basis)
        adjust = 220
        for i in range(round(new_img.size[0]/10)):
            for j in range(round(new_img.size[1]/10)):
                r, g, b = new_img.getpixel((i*10, j*10))
                if (r, g, b) == (0, 0, 0):
                    new_pixel = np.array(invtransform_vector((127, random.randint(-127,127), random.randint(-127,127)), (basis)))
                    new_pixel = new_pixel / adjust * 127
                    new_pixel = new_pixel + 127
                    new_pixel = new_pixel.astype(int)
                    
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), tuple(new_pixel))
                else:
                    new_pixel = np.array(invtransform_vector((-127, random.randint(-127,127), random.randint(-127,127)), (basis)))
                    new_pixel = new_pixel / adjust * 255
                    new_pixel = new_pixel / 2 + 127
                    new_pixel = new_pixel.astype(int)

                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), tuple(new_pixel))
    elif enc == "RANDOMON_BSHUFFLEv2":  # uses o.n.basis + noise
        norm = np.linalg.norm(np.array([1,1]))
        basis = random_onbasis()
        amplitude = 0.2
        basis = basis + noise(amplitude)
        print(basis)
        adjust = 220
        for i in range(round(new_img.size[0]/10)):
            for j in range(round(new_img.size[1]/10)):
                r, g, b = new_img.getpixel((i*10, j*10))
                if (r, g, b) == (0, 0, 0):
                    new_pixel = np.array(invtransform_vector((127, random.randint(-127,127), random.randint(-127,127)), (basis)))
                    new_pixel = new_pixel / adjust * 127
                    new_pixel = new_pixel + 127
                    new_pixel = new_pixel.astype(int)
                    
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), tuple(new_pixel))
                else:
                    new_pixel = np.array(invtransform_vector((-127, random.randint(-127,127), random.randint(-127,127)), (basis)))
                    new_pixel = new_pixel / adjust * 255
                    new_pixel = new_pixel / 2 + 127
                    new_pixel = new_pixel.astype(int)

                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), tuple(new_pixel))
    elif enc == "RANDOM_BSHUFFLE":  # uses any basis
        basis = random_normalbasis(0.5)
        amplitude = 0.2
        #basis = basis + noise(amplitude)
        print(basis)
        adjust = 220
        for i in range(round(new_img.size[0]/10)):
            for j in range(round(new_img.size[1]/10)):
                r, g, b = new_img.getpixel((i*10, j*10))
                if (r, g, b) == (0, 0, 0):
                    new_pixel = np.array(invtransform_vector((127, random.randint(-127,127), random.randint(-127,127)), (basis)))
                    new_pixel = new_pixel / adjust * 127
                    new_pixel = new_pixel + 127
                    new_pixel = new_pixel.astype(int)
                    
                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), tuple(new_pixel))
                else:
                    new_pixel = np.array(invtransform_vector((-127, random.randint(-127,127), random.randint(-127,127)), (basis)))
                    new_pixel = new_pixel / adjust * 255
                    new_pixel = new_pixel / 2 + 127
                    new_pixel = new_pixel.astype(int)

                    for k in range(100):
                        new_img.putpixel((i*10+int(k/10),j*10+k%10), tuple(new_pixel))



    new_img.save("result.png")

    return new_img

qr = qr_gen(999999999)
qr_encrypt(qr, "RED_BSHUFFLE")
