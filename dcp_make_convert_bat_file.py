import my_xml
import os
import subprocess
import argparse


ffmpeg_path = r"C:\software\ffmpeg-20131208-git-ae33007-win32-static\ffmpeg-20131208-git-ae33007-win32-static\bin\ffmpeg.exe"
asdcp_path = r"C:\software\asdcp\asdcp-test.exe"

def parse_xml(xml):
    try:
        f = open(xml, 'r')
        pkl_xml = f.read()
        my_xml_obj = my_xml.parse(pkl_xml)
        f.close()
    except my_xml.MyXmlError:
        f.close()
        return None
    return my_xml_obj
    
def get_assets(xml_file):
    parsed = parse_xml(xml_file)
    return parsed.PackingList.AssetList.Asset
    
def get_xml_path(id, ASSETMAP):
    parsed = parse_xml(ASSETMAP)
    for x in parsed.AssetMap.AssetList.Asset:
        if x.Id == id:
            return x.ChunkList[0].Chunk.Path.value
    return False
    
def parse_cpl_mxf(cpl, ASSETMAP):
    parsed = parse_xml(cpl)
    mxf_list = []
    for reel in parsed.CompositionPlaylist.ReelList.Reel:
        try:
            mxf_list.append({"mainpicture_id": reel.AssetList.MainPicture.Id.value, "mainpicture_name": get_xml_path(reel.AssetList.MainPicture.Id.value, ASSETMAP),
                            "mainsound_id": reel.AssetList.MainSound.Id.value, "mainsound_name": get_xml_path(reel.AssetList.MainSound.Id.value, ASSETMAP) })
        except AttributeError:
            mxf_list.append({"mainpicture_id": parsed.CompositionPlaylist.ReelList.Reel.AssetList.MainPicture.Id.value, 
                            "mainpicture_name": get_xml_path(parsed.CompositionPlaylist.ReelList.Reel.AssetList.MainPicture.Id.value, ASSETMAP),
                            "mainsound_id": parsed.CompositionPlaylist.ReelList.Reel.AssetList.MainSound.Id.value, 
                            "mainsound_name": get_xml_path(parsed.CompositionPlaylist.ReelList.Reel.AssetList.MainSound.Id.value, ASSETMAP) })
            break
    return mxf_list
    
def build_mxf_data(PKL, ASSETMAP):
    os.chdir(os.path.dirname(PKL))
    assets = get_assets(PKL)
    mxf_data = []
    for asset in assets:
        if asset.Type == "text/xml;asdcpKind=CPL":
           cpl_data = parse_cpl_mxf(get_xml_path(asset.Id, ASSETMAP), ASSETMAP)
           master_pic_ids = [mxf['mainpicture_id'] for mxf in mxf_data]
           for cpl_mxf in cpl_data:
               if not cpl_mxf['mainpicture_id'] in master_pic_ids:
                   mxf_data.append(cpl_mxf)
    return mxf_data
    
def create_batch_file(pkl, assetmap, output_file, output_dir):
    batch = ""
    for reel in build_mxf_data(pkl, assetmap):
        video_in = os.path.join(os.path.dirname(pkl), reel['mainpicture_name'])
        video_out = os.path.join(output_dir, reel['mainpicture_name']).replace(".mxf",".mov").replace(".MXF",".mov")
        batch += "%s -i %s -codec:v prores_ks -profile:v 2 %s\n\n" % (ffmpeg_path, video_in, video_out)
        audio_in = os.path.join(os.path.dirname(pkl), reel['mainsound_name'])
        audio_out = os.path.join(output_dir, reel['mainsound_name']).replace(".mxf",".wav").replace(".MXF",".wav")
        batch += "%s -x  %s %s\n\n" % (asdcp_path, audio_out, audio_in)
    with open(output_file, 'w') as f:
        
def create_bash_file(pkl, assetmap, output_file, output_dir):
    bash = ""
    for reel in build_mxf_data(pkl, assetmap):
        video_in = os.path.join(os.path.dirname(pkl), reel['mainpicture_name'])
        video_out = os.path.join(output_dir, reel['mainpicture_name']).replace(".mxf",".mov").replace(".MXF",".mov")
        bash += "%s -i %s -codec:v prores_ks -profile:v 2 %s;\n\n" % (ffmpeg_path, video_in, video_out)
        audio_in = os.path.join(os.path.dirname(pkl), reel['mainsound_name'])
        audio_out = os.path.join(output_dir, reel['mainsound_name']).replace(".mxf",".wav").replace(".MXF",".wav")
        bash += "%s -x  %s %s;\n\n" % (asdcp_path, audio_out, audio_in)
    with open(output_file, 'w') as f:
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser("DCP Windows or Bash Script Creator for Converting MXFs")
    parser.add_argument("-p", "--pkl", help="path to PKL", nargs="?")
    parser.add_argument("-a", "--assetmap", help="path to ASSETMAP", nargs="?")
    parser.add_argument("-o", "--output_file", help="path to output file", nargs="?")
    parser.add_argument("-m", "--output_dir", help="path to save mov files", nargs="?")
    parser.add_argument("-b", "--bash", help="create bash script instead of batch", nargs="?", const=True)
    args = parser.parse_args()
    
    if not args.pkl or not args.assetmap or not args.output_file or not args.output_dir:
        print "Must provide -p PKL -a ASSETMAP -o output_file -m output_dir"
    elif args.bash:
        create_bash_file(args.pkl, args.assetmap, args.output_file, args.output_dir)
    else:
        create_batch_file(args.pkl, args.assetmap, args.output_file, args.output_dir)