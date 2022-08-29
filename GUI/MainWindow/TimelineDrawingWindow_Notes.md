

## Loading Data:

Adding menu items via Qt Creator to the .ui file creates actions



In __init__:


        self.labjackDataFilesystemLoader = LabjackFilesystemLoader([], parent=self)
        self.labjackDataFilesystemLoader.loadingLabjackDataFilesComplete.connect(self.on_labjack_files_loading_complete)
        self.activeGlobalTimelineTimesChanged.connect(self.labjackDataFilesystemLoader.on_active_global_timeline_times_changed)
        


    #################################################
    # actionImport_general_h5_Data
    @pyqtSlot()
    def on_user_general_h5_data_load(self):
        # Called when the user selects "Import Actigraphy data..." from the main menu.
        print("TimelineDrawingWindow.on_user_general_h5_data_load()")
        # Show a dialog that asks the user for their export path
        # exportFilePath = self.on_exportFile_selected()

        path = QFileDialog.getOpenFileName(self, 'Open .h5 Data File', os.getenv('HOME'), 'h5(*.h5)')
        importFilePath = path[0]
        if importFilePath == '':
            print("User canceled the import!")
            return
        else:
            print("Importing data file at path {}...".format(importFilePath))
            self.get_general_h5_data_files_loader().add_actigraphy_file_path(importFilePath)

    # TODO: MAke a general "data_files_loader" out of labjack_data_files_loader

    def get_general_h5_data_files_loader(self):
        return self.actigraphyDataFilesystemLoader

    @pyqtSlot()
    def on_general_h5_files_loading_complete(self):
        print("TimelineDrawingWindow.on_general_h5_files_loading_complete()...")
        activeLoader = self.get_general_h5_data_files_loader()
        ## UNIMPLEMENTED!