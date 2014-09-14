import my_xml
import os
import subprocess
import argparse

subtitle_edit_path = r"C:\Program Files\Subtitle Edit\SubtitleEdit.exe"

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
    
def parse_cpl_subtitles(cpl, subtitle_list, ASSETMAP):
    parsed = parse_xml(cpl)
    for reel in parsed.CompositionPlaylist.ReelList.Reel:
        if not hasattr(reel.AssetList, "MainSubtitle"):
            continue
        try:
            language = reel.AssetList.MainSubtitle.Language.value
        except:
            language = reel.AssetList.MainSubtitle.Id.value[-6:]
        subtitle_list.append({"subtitle_id": reel.AssetList.MainSubtitle.Id.value, "video_id": reel.AssetList.MainPicture.Id.value, 
                              "video_name": get_xml_path(reel.AssetList.MainPicture.Id.value, ASSETMAP), "language": language,
                              "subtitle_name":  get_xml_path(reel.AssetList.MainSubtitle.Id.value, ASSETMAP)})
    return subtitle_list

def build_subtitle_data(PKL, ASSETMAP):
    os.chdir(os.path.dirname(PKL))
    assets = get_assets(PKL)
    subtitle_data = []
    for asset in assets:
        if asset.Type == "text/xml;asdcpKind=CPL":
           subtitle_data = parse_cpl_subtitles(get_xml_path(asset.Id, ASSETMAP), subtitle_data, ASSETMAP)
    return subtitle_data
    
def convert_subtitles(subtitle_data, output_dir):
    for subtitle in subtitle_data:
        subprocess.check_call(r'%s /convert %s subrip /outputfolder:%s' % (subtitle_edit_path, subtitle['subtitle_name'], output_dir), shell=True)
        subrip_name = subtitle['video_name'].replace('.mxf', '') + '_' + subtitle['language'] + '.srt' 
        os.rename(os.path.join(output_dir, os.path.basename(subtitle['subtitle_name'].replace('.xml', '.srt'))), os.path.join(output_dir, subrip_name))
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser("DCP Batch Subtitle Converter")
    parser.add_argument("-p", "--pkl", help="path to PKL", nargs="?")
    parser.add_argument("-a", "--assetmap", help="path to ASSETMAP", nargs="?")
    parser.add_argument("-o", "--output_dir", help="path to output directory", nargs="?")
    args = parser.parse_args()
    
    if not args.pkl or not args.assetmap or not args.output_dir:
        print "Must provide -p PKL -a ASSETMAP -o output_directory"
    else:
        subtitle_data = build_subtitle_data(args.pkl, args.assetmap)
        convert_subtitles(subtitle_data, args.output_dir)
