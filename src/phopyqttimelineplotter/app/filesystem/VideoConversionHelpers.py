# Handbrake Encoding Helpers
# VideoConversionHelpers.py

import json


# from phopyqttimelineplotter.app.filesystem.VideoConversionHelpers import HandbrakeConversionQueue, save_handbrake_conversion_queue

# @dataclass
class HandbrakeConversionQueue:
    # sourcePath: str
    # destFile: str

    def __init__(self, sourcePath, destFile):
        super(HandbrakeConversionQueue, self).__init__()
        self.sourcePath = sourcePath
        self.destFile = destFile

    def __str__(self):
        return "(source: {0}, dest: {1})".format(self.sourcePath, self.destFile)

    # def get_json_job(self, with_index):
        # jsonJobTemplate = """\
        #   {
        #     "Job": {
        #     "Audio": {
        #         "AudioList": [],
        #         "CopyMask": [
        #         "copy:aac",
        #         "copy:ac3",
        #         "copy:dtshd",
        #         "copy:dts",
        #         "copy:eac3",
        #         "copy:flac",
        #         "copy:mp3",
        #         "copy:truehd"
        #         ],
        #         "FallbackEncoder": "ac3"
        #     },
        #     "Destination": {
        #         "ChapterList": [
        #         {
        #             "Name": "Chapter 1"
        #         }
        #         ],
        #         "ChapterMarkers": true,
        #         "AlignAVStart": true,
        #         "File": "{destFile}",
        #         "Mp4Options": {
        #         "IpodAtom": false,
        #         "Mp4Optimize": false
        #         },
        #         "Mux": "mp4"
        #     },
        #     "Filters": {
        #         "FilterList": [
        #         {
        #             "ID": 4,
        #             "Settings": {
        #             "mode": "7"
        #             }
        #         },
        #         {
        #             "ID": 3,
        #             "Settings": {
        #             "block-height": "16",
        #             "block-thresh": "40",
        #             "block-width": "16",
        #             "filter-mode": "2",
        #             "mode": "3",
        #             "motion-thresh": "1",
        #             "spatial-metric": "2",
        #             "spatial-thresh": "1"
        #             }
        #         },
        #         {
        #             "ID": 11,
        #             "Settings": {
        #             "crop-bottom": "0",
        #             "crop-left": "0",
        #             "crop-right": "0",
        #             "crop-top": "0",
        #             "height": "512",
        #             "width": "640"
        #             }
        #         },
        #         {
        #             "ID": 6,
        #             "Settings": {
        #             "mode": "2",
        #             "rate": "27000000/900000"
        #             }
        #         }
        #         ]
        #     },
        #     "PAR": {
        #         "Num": 1,
        #         "Den": 1
        #     },
        #     "Metadata": {},
        #     "SequenceID": 0,
        #     "Source": {
        #         "Angle": 1,
        #         "Range": {
        #         "Type": "chapter",
        #         "Start": 1,
        #         "End": 1
        #         },
        #         "Title": {titleIndex},
        #         "Path": "{sourceFile}"
        #     },
        #     "Subtitle": {
        #         "Search": {
        #         "Burn": true,
        #         "Default": false,
        #         "Enable": true,
        #         "Forced": true
        #         },
        #         "SubtitleList": []
        #     },
        #     "Video": {
        #         "Encoder": "x264",
        #         "Level": "4.0",
        #         "TwoPass": false,
        #         "Turbo": false,
        #         "ColorMatrixCode": 0,
        #         "Options": "",
        #         "Preset": "fast",
        #         "Profile": "main",
        #         "Quality": 22.0,
        #         "QSV": {
        #         "Decode": false,
        #         "AsyncDepth": 0
        #         }
        #     }
        #     }
        # },\
        # """

    def get_json_job(self, with_index):
        # jsonJobTemplate = {'Job': {'Audio': {'AudioList': [], 'CopyMask': ['copy:aac', 'copy:ac3', 'copy:dtshd', 'copy:dts', 'copy:eac3', 'copy:flac', 'copy:mp3', 'copy:truehd'], 'FallbackEncoder': 'ac3'}, 'Destination': {'ChapterList': [{'Name': 'Chapter 1'}], 'ChapterMarkers': True, 'AlignAVStart': False, 'File': '\\\\10.17.158.49\\ServerInternal-01\\Transcoded Videos\\BB00\\BehavioralBox_B00_T20190916-1711360679.mp4', 'Mp4Options': {'IpodAtom': False, 'Mp4Optimize': False}, 'Mux': 'mp4'}, 'Filters': {'FilterList': [{'ID': 4, 'Settings': {'mode': '7'}}, {'ID': 3, 'Settings': {'block-height': '16', 'block-thresh': '40', 'block-width': '16', 'filter-mode': '2', 'mode': '3', 'motion-thresh': '1', 'spatial-metric': '2', 'spatial-thresh': '1'}}, {'ID': 11, 'Settings': {'crop-bottom': '0', 'crop-left': '0', 'crop-right': '0', 'crop-top': '0', 'height': '512', 'width': '640'}}, {'ID': 6, 'Settings': {'mode': '0'}}]}, 'PAR': {'Num': 1, 'Den': 1}, 'Metadata': {}, 'SequenceID': 0, 'Source': {'Angle': 1, 'Range': {'Type': 'chapter', 'Start': 1, 'End': 1}, 'Title': 213, 'Path': '\\\\10.17.158.49\\ServerInternal-00\\Videos\\BB00\\BehavioralBox_B00_T20190916-1711360679.mkv'}, 'Subtitle': {'Search': {'Burn': False, 'Default': False, 'Enable': False, 'Forced': False}, 'SubtitleList': []}, 'Video': {'Encoder': 'x264', 'Level': '4.0', 'TwoPass': False, 'Turbo': False, 'ColorMatrixCode': 0, 'Options': '', 'Preset': 'fast', 'Profile': 'main', 'Quality': 22.0, 'QSV': {'Decode': False, 'AsyncDepth': 0}}}}
        # jsonJobTemplate.format(destFile=self.destFile, titleIndex=str(with_index), sourceFile=self.sourcePath)
        jsonJobTemplate = {'Job': {'Audio': {'AudioList': [], 'CopyMask': ['copy:aac', 'copy:ac3', 'copy:dtshd', 'copy:dts', 'copy:eac3', 'copy:flac', 'copy:mp3', 'copy:truehd'], 'FallbackEncoder': 'ac3'}, 'Destination': {'ChapterList': [{'Name': 'Chapter 1'}], 'ChapterMarkers': True, 'AlignAVStart': False, 'File': self.destFile, 'Mp4Options': {'IpodAtom': False, 'Mp4Optimize': False}, 'Mux': 'mp4'}, 'Filters': {'FilterList': [{'ID': 4, 'Settings': {'mode': '7'}}, {'ID': 3, 'Settings': {'block-height': '16', 'block-thresh': '40', 'block-width': '16', 'filter-mode': '2', 'mode': '3', 'motion-thresh': '1', 'spatial-metric': '2', 'spatial-thresh': '1'}}, {'ID': 11, 'Settings': {'crop-bottom': '0', 'crop-left': '0', 'crop-right': '0', 'crop-top': '0', 'height': '512', 'width': '640'}}, {'ID': 6, 'Settings': {'mode': '0'}}]}, 'PAR': {'Num': 1, 'Den': 1}, 'Metadata': {}, 'SequenceID': 0, 'Source': {'Angle': 1, 'Range': {'Type': 'chapter', 'Start': 1, 'End': 1}, 'Title': with_index, 'Path': self.sourcePath}, 'Subtitle': {'Search': {'Burn': False, 'Default': False, 'Enable': False, 'Forced': False}, 'SubtitleList': []}, 'Video': {'Encoder': 'x264', 'Level': '4.0', 'TwoPass': False, 'Turbo': False, 'ColorMatrixCode': 0, 'Options': '', 'Preset': 'fast', 'Profile': 'main', 'Quality': 22.0, 'QSV': {'Decode': False, 'AsyncDepth': 0}}}}
        return jsonJobTemplate

    

def load_handbrake_conversion_queue(file_path="C:/Common/temp/10-29-2019-BB0-mkv-to-mp4-queue-serverAddress.json"):
    outputConversionQueue = []
    with open(file_path) as json_file:
        data = json.load(json_file)
        # print(data)
        for aJob in data:
            theJobObj = aJob['Job']
            # print(theJobObj)
            # print(json.dumps(theJobObj, indent=4))
            currDest = theJobObj['Destination']
            currDestFile = currDest['File']
            currSource = theJobObj['Source']
            currSourcePath = currSource['Path']
            if (currDestFile and currSourcePath):
                outputConversionQueue.append(HandbrakeConversionQueue(currSourcePath, currDestFile))
        return outputConversionQueue

    # loadedJson = json.load(file_path)
    # print(loadedJson)
    return None


def save_handbrake_conversion_queue(conversionJobObjects, output_file="C:/Common/temp/11-19-2019-BB0-mkv-to-mp4-queue-phoVideoConversionHelperTest.json"):
    out_json_array = []
    for (aJobIndex, aConversionJob) in enumerate(conversionJobObjects):
        newJobAsJSON = aConversionJob.get_json_job(aJobIndex)
        # jstr = json.dumps(newJobAsJSON, indent=4)
        # print(jstr)
        # out_json_array.append(jstr)
        out_json_array.append(newJobAsJSON)
        

    with open(output_file, 'w') as outfile:
        json.dump(out_json_array, outfile)
        print("wrote json to file: {0}".format(output_file))





if __name__ == "__main__":
    out_json_array = []
    out_data = load_handbrake_conversion_queue()

    save_handbrake_conversion_queue(out_data)


    # for (aJobIndex, aConversionJob) in enumerate(out_data):
    #     newJobAsJSON = aConversionJob.get_json_job(aJobIndex)
    #     # print(aConversionJob)
    #     jstr = json.dumps(newJobAsJSON, indent=4)
    #     print(jstr)
    #     out_json_array.append(jstr)

    # print(out_data[0].get_json_job(0))

    # print(json.dumps(out_data, indent=4))
    # print(out)