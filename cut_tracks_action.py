#!/usr/bin/env python
import pcbnew
import os.path
import wx

class CutTracksAtLine(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Cut tracks at line"
        self.description = "Cuts all selected tracks at an intersecting line"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')

    def line_intersection(self, line1, line2):
        '''
        Calculate the intersection point of two lines.
        Args:
            line1, line2: Tuple of two points each, representing the start and end points of the lines.
        Returns:
            Tuple of three values:
            - First value is a boolean indicating if the lines intersect.
            - Second and third values are the x and y coordinates of the intersection point.
        '''
        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            return False, None , None
        
        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div

        # Check if the intersection point is within the bounds of both line segments
        if min(line1[0][0], line1[1][0]) <= x <= max(line1[0][0], line1[1][0]) and min(line1[0][1], line1[1][1]) <= y <= max(line1[0][1], line1[1][1]) and min(line2[0][0], line2[1][0]) <= x <= max(line2[0][0], line2[1][0]) and min(line2[0][1], line2[1][1]) <= y <= max(line2[0][1], line2[1][1]):
            return True, x, y
        else:
            return False, None, None

    def Run(self):
        board = pcbnew.GetBoard() # get the current board

        # get the selected tracks
        selected_tracks: list[pcbnew.PCB_TRACK] = [
                    track for track in pcbnew.GetCurrentSelection()
                    if type(track).__name__ == 'PCB_TRACK'
                ]

        # get the selected lines
        selected_lines: list[pcbnew.PCB_SHAPE] = [
                    line for line in pcbnew.GetCurrentSelection()
                    if type(line).__name__ == 'PCB_SHAPE'
                ]

        if (len(selected_tracks) == 0) or (len(selected_lines) == 0):
            dlg = wx.MessageDialog(None, 'Please select at least one track and one line.', 'CutTracksAtLine plugin', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        cut_count = 0 # count the number of cuts made

        for line in selected_lines:
            # Get the start and end points of the cutting line
            line_start = (line.GetStart()[0], line.GetStart()[1])
            line_end = (line.GetEnd()[0], line.GetEnd()[1])
            cutting_line = (line_start, line_end)

            new_track_list = [] # list to store the new tracks created by cutting the original tracks

            for track in selected_tracks:
                # Get the start and end points of the track
                track_start = pcbnew.VECTOR2I(int(track.GetStart()[0]), int(track.GetStart()[1]))
                track_end = pcbnew.VECTOR2I(int(track.GetEnd()[0]), int(track.GetEnd()[1]))
                track_line = (track_start, track_end)

                # Check if the track intersects with the line and get the intersection point
                does_intersect, intersection_x, intersection_y = self.line_intersection(cutting_line, track_line)
                if does_intersect:  
                    intersection = pcbnew.VECTOR2I(int(intersection_x), int(intersection_y))

                    # Cut the track at the intersection point
                    track.SetEnd(intersection)

                    # Create a new track from the intersection point to the original end point
                    new_track = pcbnew.PCB_TRACK(track) # copy the original track
                    new_track.SetStart(intersection)
                    new_track.SetEnd(track_end)
                    new_track.SetWidth(track.GetWidth()) # set the width of the new track to the width of the original track
                    new_track.SetLayer(track.GetLayer()) # set the layer of the new track to the layer of the original track
                    new_track.SetNet(track.GetNet()) # set the net of the new track to the net of the original track
                    board.Add(new_track) # add the new track to the board
                    new_track_list.append(new_track)
                    cut_count += 1

            selected_tracks.extend(new_track_list) # add the new tracks to the selected tracks list to allow cutting by multiple lines

        pcbnew.Refresh() # refresh the board view, this prevents added tracks from being invisible

        dlg = wx.MessageDialog(None, f'Successfully cut tracks at {cut_count} points.', 'CutTracksAtLine plugin', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()