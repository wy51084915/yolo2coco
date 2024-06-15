# -*- encoding: utf-8 -*-
# @Author: SWHL
# @Contact: liekkaskono@163.com
import argparse
import imghdr
import random
import shutil
from pathlib import Path

from tqdm import tqdm


class LabelImgToYOLOV5():
    def __init__(self, root_dir, out_dir, val_ratio, have_test, test_ratio):
        self.root_dir = Path(root_dir)
        self.verify_exists(self.root_dir)

        self.out_dir = Path(out_dir)
        self.out_img_dir = self.out_dir / 'images'
        self.out_label_dir = self.out_dir / 'labels'
        self.out_non_label_dir = self.out_dir / 'non_labels'

        self.classes_path = self.root_dir / 'classes.txt'
        self.verify_exists(self.classes_path)
        self.cp_file(self.classes_path, dst_dir=self.out_dir)

        self.val_ratio = val_ratio
        self.have_test = have_test
        self.test_ratio = test_ratio

    def __call__(self):
        img_list = self.get_img_list()
        if img_list:
            img_list = self.gen_image_label_dir(img_list)
        else:
            return ValueError(f'{self.root_dir} is corrupted.')

        split_list = self.get_train_val_test_list(img_list,
                                                  ratio=self.val_ratio,
                                                  have_test=self.have_test,
                                                  test_ratio=self.test_ratio)
        train_list, val_list, test_list = split_list
        self.write_txt(self.out_dir / 'train.txt', train_list)
        self.write_txt(self.out_dir / 'val.txt', val_list)
        if test_list:
            self.write_txt(self.out_dir / 'test.txt', test_list)
        print(f'Successfully convert, detail in {self.out_dir}')

    @staticmethod
    def verify_exists(file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f'The {file_path} is not exists!!!')

    def get_img_list(self):
        img_list = []
        all_list = self.root_dir.glob('*.*')
        for one in all_list:
            cur_suffix = one.suffix
            if cur_suffix != '.txt':
                img_list.append(one)
        return img_list

    def gen_image_label_dir(self, img_list):
        new_image_list = []
        for img_path in tqdm(img_list):
            right_label_path = img_path.with_name(f'{img_path.stem}.txt')
            if right_label_path.exists() \
                    and self.read_txt(str(right_label_path)):
                self.cp_file(img_path, dst_dir=self.out_img_dir)
                self.cp_file(right_label_path, dst_dir=self.out_label_dir)

                new_image_list.append(img_path)
            else:
                self.cp_file(img_path, dst_dir=self.out_non_label_dir)
        return new_image_list

    def get_train_val_test_list(self, img_list, ratio=0.2, have_test=True,
                                test_ratio=0.2):
        random.shuffle(img_list)
        img_list = [f'{self.out_img_dir / img_path.name}'
                    for img_path in img_list]
        len_img = len(img_list)
        if have_test:
            split_idx_first = int(len_img * ratio)
            split_idx_second = int(len_img * (ratio + test_ratio))

            val_list = img_list[:split_idx_first]
            train_list = img_list[split_idx_second:]
            test_list = img_list[split_idx_first:split_idx_second]
        else:
            split_node = int(len_img * ratio)

            val_list = img_list[:split_node]
            train_list = img_list[split_node:]
            test_list = None
        return train_list, val_list, test_list

    @staticmethod
    def mkdir(dir_path):
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def read_txt(txt_path: str) -> list:
        with open(txt_path, 'r', encoding='utf-8') as f:
            data = list(map(lambda x: x.rstrip('\n'), f))
        return data

    @staticmethod
    def write_txt(save_path: str, content: list, mode='w'):
        if isinstance(content, str):
            content = [content]
        with open(save_path, mode, encoding='utf-8') as f:
            for value in content:
                f.write(f'{value}\n')

    @staticmethod
    def get_img_format(img_path):
        with open(img_path, 'rb') as f:
            return imghdr.what(f)

    def cp_file(self, file_path: Path, dst_dir: Path):
        if not file_path.exists():
            return FileExistsError(file_path)

        if not dst_dir.exists():
            self.mkdir(dst_dir)

        dst_file_path = dst_dir / file_path.name
        shutil.copy2(str(file_path), str(dst_file_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--src_dir', type=str)
    parser.add_argument('--out_dir', type=str)
    parser.add_argument('--val_ratio', type=float, default=0.2)
    parser.add_argument('--have_test', type=bool, default=False)
    parser.add_argument('--test_ratio', type=float, default=0.2)
    args = parser.parse_args()

    converter = LabelImgToYOLOV5(args.src_dir, args.out_dir, args.val_ratio,
                                 args.have_test, args.test_ratio)
    converter()
    print(f'Successfully output to the {args.out_dir}')
