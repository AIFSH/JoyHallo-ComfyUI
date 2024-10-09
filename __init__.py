import os,sys
import folder_paths
import os.path as osp
now_dir = osp.dirname(osp.abspath(__file__))
config_file = osp.join(now_dir, "inference.yaml")
pretrained_dir = osp.join(now_dir,"pretrained_models")
wav2vec_dir = osp.join(pretrained_dir,"chinese-wav2vec2-base")
audio_separator_dir = osp.join(pretrained_dir,"audio_separator")
base_model_path = osp.join(pretrained_dir,"stable-diffusion-v1-5")
vae_model_path = osp.join(pretrained_dir,"sd-vae-ft-mse")
joyhallo_path = osp.join(pretrained_dir,"JoyHallo-v1")

import time
import shutil
import torchaudio
import numpy as np
from PIL import Image
from huggingface_hub import snapshot_download,hf_hub_download
from .inference import load_config, inference_process

class JoyHalloNode:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required":{
                "audio":("AUDIO",),
                "image":("IMAGE",),
                "inference_steps":("INT",{
                    "default":40
                }),
                "cfg_scale":("FLOAT",{
                    "default":3.5
                }),
                "seed":("INT",{
                    "default":42
                }),
            }
        }
    
    RETURN_TYPES = ("VIDEO",)
    #RETURN_NAMES = ("image_output_name",)

    FUNCTION = "gen_video"

    #OUTPUT_NODE = False

    CATEGORY = "AIFSH_JoyHallo"

    def gen_video(self,audio,image,inference_steps,cfg_scale,seed):
        config = load_config(config_file)
        config.inference_steps = inference_steps
        config.cfg_scale = cfg_scale
        config.seed = seed
        if not osp.exists(osp.join(base_model_path,"unet","diffusion_pytorch_model.safetensors")):
            snapshot_download(repo_id="fudan-generative-ai/hallo",
                              local_dir=pretrained_dir,
                              ignore_patterns=["*et.pth"])

        if not osp.exists(osp.join(wav2vec_dir,"chinese-wav2vec2-base-fairseq-ckpt.pt")):
            snapshot_download(repo_id="TencentGameMate/chinese-wav2vec2-base",
                              local_dir=wav2vec_dir)
        config.wav2vec_config.model_path = wav2vec_dir

        config.audio_separator.model_path = osp.join(audio_separator_dir,"Kim_Vocal_2.onnx")
        if not osp.exists(config.audio_separator.model_path):
            hf_hub_download(repo_id="seanghay/uvr_models",
                              local_dir=audio_separator_dir,
                              filename="Kim_Vocal_2.onnx")
        
        '''
        if not osp.exists(osp.join(base_model_path,"unet","diffusion_pytorch_model.fp16.safetensors")):
            snapshot_download(repo_id="stable-diffusion-v1-5/stable-diffusion-v1-5",
                              local_dir=base_model_path,
                              allow_patterns=["*fp16*","*json","*txt"])
        '''
        config.base_model_path = base_model_path
        '''
        if not osp.exists(osp.join(vae_model_path,"diffusion_pytorch_model.safetensors")):
            snapshot_download(repo_id="stabilityai/sd-vae-ft-mse",
                              local_dir=vae_model_path,
                              allow_patterns=["*safetensors","*json"])
        '''
        config.vae_model_path = vae_model_path

        config.face_analysis_model_path = osp.join(pretrained_dir,"face_analysis/models")
        config.mm_path = osp.join(pretrained_dir,"motion_module/mm_sd_v15_v2.ckpt")
        config.output_dir = folder_paths.get_output_directory()

        # jdh-algo/JoyHallo-v1
        config.audio_ckpt_dir = osp.join(joyhallo_path,"net.pth")
        if not osp.exists(config.audio_ckpt_dir):
            snapshot_download(repo_id="jdh-algo/JoyHallo-v1",
                              local_dir=joyhallo_path)
        
        img_np = image.numpy()[0] * 255
        img_pil = Image.fromarray(img_np.astype(np.uint8))
        save_dir = osp.join(config.output_dir,config.exp_name)
        os.makedirs(save_dir,exist_ok=True)
        ref_img_path = osp.join(save_dir,"refimg.jpg")
        img_pil.save(ref_img_path)

        audio_path = osp.join(save_dir,"audio.wav")
        torchaudio.save(audio_path,audio['waveform'].squeeze(0),audio['sample_rate'])
        config.ref_img_path = [ref_img_path]
        config.audio_path = [audio_path]
        print(config)
        inference_process(config)
        tmp_output_file = osp.join(save_dir,"0_refimg_audio.mp4")
        output_file = osp.join(config.output_dir,f"{time.time_ns()}.mp4")
        shutil.copy(tmp_output_file,output_file)
        return (output_file,)

WEB_DIRECTORY = "./js"
from .util_nodes import LoadVideo, PreViewVideo
NODE_CLASS_MAPPINGS = {
    "LoadVideo": LoadVideo,
    "PreViewVideo":PreViewVideo,
    "JoyHalloNode": JoyHalloNode
}