# pip install pyzbar pillow matplotlib numpy opencv-python
import copy
import pyzbar.pyzbar as pyzbar
import matplotlib.pylab as plt
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
import PIL.ImageOps
import numpy as np

key_vector = np.array([1,0,0])
key_basis = [np.array([1,1,0]), np.array([0,1,1]), np.array([1,0,1])]

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

def qr_reader(img):
    gray = img.convert('LA')
    plt.imshow(gray)
    gray.save("decoding.png")
    decoded = pyzbar.decode(gray)
    print(decoded)

    if len(decoded) == 0:
        return None
    
    data = []
    for d in decoded:
        data.append(d.data.decode('utf-8'))
    return data

def qr_decoder(img, enc):
    new_img = copy.deepcopy(img)
    GaussianBlur = ImageFilter.GaussianBlur(1)
    new_img = new_img.filter(GaussianBlur)
    if enc == "":
        pass
    elif enc == "RED_SHUFFLE" or enc == "RED_BSHUFFLE":
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                r, g, b = new_img.getpixel((i, j))
                new_img.putpixel((i,j), (r, r, r))
        new_img = PIL.ImageOps.invert(new_img)
    elif enc == "GREEN_SHUFFLE" or enc == "GREEN_BSHUFFLE":
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                r, g, b = new_img.getpixel((i, j))
                new_img.putpixel((i,j), (g, g, g))
        new_img = PIL.ImageOps.invert(new_img)
        pass
    elif enc == "BLUE_SHUFFLE" or enc == "BLUE_BSHUFFLE":
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                r, g, b = new_img.getpixel((i, j))
                new_img.putpixel((i,j), (b, b, b))
        new_img = PIL.ImageOps.invert(new_img)
        pass
    elif enc == "YELLOW_SHUFFLE" or enc == "YELLOW_BSHUFFLE":
        norm = np.linalg.norm(np.array([1,1]))
        basis = [np.array([1,1,0])/norm, np.array([0,1,1])/norm, np.array([1,0,1])/norm]
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                pixel = np.array(new_img.getpixel((i, j)))
                ycm = tuple(np.array(transform_vector(tuple(pixel), basis)).astype(int))
                new_img.putpixel((i,j), (ycm[0], ycm[0], ycm[0]))
        new_img = PIL.ImageOps.invert(new_img)
        pass
    elif enc == "ONVECTOR_BSHUFFLE":
        norm = np.linalg.norm(np.array([1,1]))
        basis = onbasis(key_vector)
        adjust = 100
        threshold = 25
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                pixel = np.array(new_img.getpixel((i, j)))
                pixel = transform_vector((pixel - 127) * adjust / 127, onbasis(key_vector))
                pixel = pixel + np.array((127, 127, 127))
                pixel = pixel.astype(int)
                new_img.putpixel((i,j), (pixel[0], pixel[0], pixel[0]))
        new_img = PIL.ImageOps.invert(new_img)
        pass
    elif enc == "NVECTOR_BSHUFFLE":
        basis = np.array([key_basis[0], key_basis[1], key_basis[2]]).T
        adjust = 220
        print(basis)
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                pixel = np.array(new_img.getpixel((i, j)))
                pixel = pixel - np.array((127, 127, 127))
                pixel = np.linalg.solve(basis, pixel)
                pixel = pixel + np.array((127, 127, 127))
                pixel = pixel / 127 * adjust
                pixel = pixel.astype(int)
                new_img.putpixel((i,j), (pixel[0], pixel[0], pixel[0]))
        new_img = PIL.ImageOps.invert(new_img)
        pass
    
    #new_img = ImageEnhance.Contrast(new_img).enhance(2)

    print("Decoded!")
    new_img.save("decoding.png")
    return new_img


test_img = Image.open('result.png')
test_img_small = test_img.resize((300, int(300/test_img.size[0]*test_img.size[1])))
test_img_reverse = PIL.ImageOps.invert(test_img)

#qr_reader(qr_decoder(test_img, "RED_BSHUFFLE"))