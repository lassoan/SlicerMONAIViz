# Copyright (c) MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import importlib
import inspect
import os
from typing import Any


class ClassUtils:
    @staticmethod
    def is_subclass(n, o, base_c):
        if inspect.isclass(o) and n != base_c:
            b = [cls.__name__ for cls in o.__bases__]
            if base_c in b:
                return True
        return False

    @staticmethod
    def get_class_of_subclass(module, base_classes) -> dict[str, Any]:
        print(f"{module} => {base_classes}")
        res: dict[str, Any] = {}
        for n, o in inspect.getmembers(module):
            if not inspect.isclass(o) or inspect.isabstract(o):
                continue

            # print(f"{n} => {o}")
            for base_c in base_classes:
                if ClassUtils.is_subclass(n, o, base_c):
                    cp = f"{o.__module__}.{o.__name__}"
                    if res.get(cp):
                        res[cp]["alias"].append(n)
                    else:
                        res[cp] = {
                            "name": o.__name__,
                            "alias": [n],
                            "class": cp,
                            "module": o.__module__,
                            "dictionary": o.__module__.endswith("dictionary"),
                            "base_class": base_c,
                            "category": ".".join(o.__module__.split(".")[:3]),
                        }
                    break

        sorted_d: dict[str, Any] = {}
        for k in sorted(res.keys()):
            v = res[k]
            v["alias"] = sorted(v["alias"])
            sorted_d[k] = v

        return sorted_d

    @staticmethod
    def args_to_expression(class_args):
        key_val = []
        for key in class_args:
            val = class_args[key]
            if isinstance(val, str):
                val = "'" + val + "'"
            elif isinstance(val, tuple) or isinstance(val, list):
                vals = []
                for v in val:
                    if isinstance(v, str):
                        v = "'" + v + "'"
                    else:
                        v = str(v)
                    vals.append(v)
                if isinstance(val, tuple):
                    val = "(" + ", ".join(vals) + ")"
                else:
                    val = "[" + ", ".join(vals) + "]"
            else:
                val = str(val)
            key_val.append(f"{key}={val}")
        return ", ".join(key_val)

    @staticmethod
    def expression_to_args(exp, handle_bool=True):
        if not exp:
            return {}

        if handle_bool:
            exp = exp.replace("=true", "=True").replace("=false", "=False")  # safe to assume
            exp = exp.replace(" true", " True").replace(" false", " False")

        def foo(**kwargs):
            return kwargs

        return eval("foo(" + exp + ")")


class MonaiUtils:
    @staticmethod
    def version():
        try:
            import monai

            return monai.__version__
        except ImportError:
            return ""

    @staticmethod
    def list_transforms(module="monai.transforms"):
        mt = importlib.import_module(module)
        return ClassUtils.get_class_of_subclass(mt, ["Transform", "MapTransform"])

    @staticmethod
    def list_bundles(auth_token=None):
        from monai.bundle import get_all_bundles_list

        return get_all_bundles_list(auth_token=auth_token)

    @staticmethod
    def download_bundle(name, bundle_dir, auth_token=None):
        from monai.bundle import download, get_bundle_versions

        # Support 1.1.0 monai (bug) for downloading bundles on Windows (pass specific version)
        version = get_bundle_versions(name, auth_token=auth_token)["latest_version"]
        download(name, version=version, bundle_dir=bundle_dir)

    @staticmethod
    def transforms_from_bundle(name, bundle_dir):
        from monai.bundle import ConfigParser

        bundle_root = os.path.join(bundle_dir, name)
        config_path = os.path.join(bundle_root, "configs", "train.json")
        if not os.path.exists(config_path):
            config_path = os.path.join(bundle_root, "configs", "train.yaml")

        bundle_config = ConfigParser()
        bundle_config.read_config(config_path)
        bundle_config.config.update({"bundle_root": bundle_root})  # type: ignore

        for k in ["train#preprocessing#transforms", "train#pre_transforms#transforms"]:
            if bundle_config.get(k):
                c = bundle_config.get_parsed_content(k, instantiate=False)
                c = [x.get_config() for x in c]
                return c

        return None

    @staticmethod
    def run_transform(name, args, data):
        import monai

        print(monai.__version__)

        exp = f"monai.transforms.{name}({args if args else ''})"
        print(exp)
        t = eval(exp)

        print(data)
        d = t(data)
        return d


"""
def main():
    transforms = MonaiUtils.list_transforms()

    print("ALL Transforms....")
    print("----------------------------------------------------------------")
    for t in transforms:
        print(f"{t} => {transforms[t]['module']}")

    modules = sorted(list({v["module"] for v in transforms.values()}))

    print("")
    print("ALL Modules....")
    print("----------------------------------------------------------------")
    for m in modules:
        print(f"{m}")
    # print(json.dumps(categories, indent=2))

    print("")
    print("ALL Bundles....")
    print("----------------------------------------------------------------")
    bundles = MonaiUtils.list_bundles()
    for b in sorted({b[0] for b in bundles}):
        print(b)

    bundle_dir = "/tmp/Slicer-sachi/slicer-monai-transforms/bundle"
    bundle_dir = "C:/Users/salle/AppData/Local/Temp/Slicer/slicer-monai-transforms/bundle"
    # MonaiUtils.download_bundle(
    #     "spleen_ct_segmentation", bundle_dir
    # )

    print("")
    print("Bundle Transforms....")
    print("----------------------------------------------------------------")
    b_transforms = MonaiUtils.transforms_from_bundle("spleen_ct_segmentation", bundle_dir)
    for t in b_transforms:
        print(f"{type(t)} => {t}")


def main2():
    data = {
        "image": "/localhome/sachi/Datasets/Radiology/Task09_Spleen/imagesTr/spleen_2.nii.gz",
        "label": "/localhome/sachi/Datasets/Radiology/Task09_Spleen/labelsTr/spleen_2.nii.gz",
    }
    MonaiUtils.run_transform(name="LoadImaged", args="keys=['image', 'label']", data=data)


if __name__ == "__main__":
    # pip_install("monai")
    # pip_install("nibabel")
    main()
"""
