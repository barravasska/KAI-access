import cv2

for i in range(1, 4):
    path = f"test_images/sakha{i}.jpg"
    img = cv2.imread(path)

    if img is None:
        print(f"{path}: tidak ditemukan")
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    score = cv2.Laplacian(gray, cv2.CV_64F).var()

    print(f"sakha{i}.jpg: {score:.2f}")