

using Autodesk.Navisworks.Api;
using Autodesk.Navisworks.Api.Plugins;
using Autodesk.Navisworks.Api.Timeliner;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace timeliner_Plugin
{
    [PluginAttribute("VIS4D_Plugin", "ADSK", ToolTip = "VIS4D Plugin", DisplayName = "VIS4D")]
    public class VIS4D : AddInPlugin

    {
        private NavisworksServer server;
        public override int Execute(params string[] parameters)
        {
            // Initialize and start the server
            try
            {
                server = new NavisworksServer(this);
                Task.Run(() => server.StartServer());
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error starting server: {ex.Message}", "Server Error",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }

            using (Form actionForm = new Form())
            {
                actionForm.Text = "Timeliner Task Manager";
                actionForm.Width = 300;
                actionForm.Height = 200;
                actionForm.FormBorderStyle = FormBorderStyle.FixedDialog;
                actionForm.StartPosition = FormStartPosition.CenterScreen;

                Button btnCreate = new Button()
                {
                    Text = "Create New Task",
                    Top = 20,
                    Left = 50,
                    Width = 200
                };

                Button btnUpdate = new Button()
                {
                    Text = "Update Existing Task",
                    Top = 60,
                    Left = 50,
                    Width = 200
                };

                Button btnDelete = new Button()
                {
                    Text = "Delete Task",
                    Top = 100,
                    Left = 50,
                    Width = 200
                };

                btnCreate.Click += (s, e) =>
                {
                    actionForm.Hide();
                    ShowCreateTaskForm();
                    actionForm.Close();
                };

                btnUpdate.Click += (s, e) =>
                {
                    actionForm.Hide();
                    ShowUpdateTaskForm();
                    actionForm.Close();
                };

                btnDelete.Click += (s, e) =>
                {
                    actionForm.Hide();
                    ShowDeleteTaskForm();
                    actionForm.Close();
                };

                actionForm.Controls.AddRange(new Control[] { btnCreate, btnUpdate, btnDelete });
                actionForm.ShowDialog();
            }
            return 0;
        }

        private void ShowCreateTaskForm()
        {
            using (Form inputForm = new Form())
            {
                inputForm.Text = "Add Timeliner Task";
                inputForm.Width = 500;
                inputForm.Height = 350;
                inputForm.FormBorderStyle = FormBorderStyle.FixedDialog;
                inputForm.StartPosition = FormStartPosition.CenterScreen;

                Label lblTaskName = new Label() { Text = "Task Name:", Top = 20, Left = 20, Width = 150 };
                TextBox txtTaskName = new TextBox() { Top = 20, Left = 180, Width = 280 };

                Label lblTaskType = new Label() { Text = "Task Type:", Top = 70, Left = 20, Width = 150 };
                ComboBox cboTaskType = new ComboBox() { Top = 70, Left = 180, Width = 280, DropDownStyle = ComboBoxStyle.DropDownList };

                var timeliner = Autodesk.Navisworks.Api.Application.ActiveDocument.GetTimeliner();
                cboTaskType.Items.AddRange(timeliner.SimulationTaskTypes.Select(t => t.DisplayName).ToArray());
                if (cboTaskType.Items.Count > 0) cboTaskType.SelectedIndex = 0;

                Label lblStartDate = new Label() { Text = "Start Date:", Top = 120, Left = 20, Width = 150 };
                DateTimePicker dtpStartDate = new DateTimePicker() { Top = 120, Left = 180, Width = 280, Format = DateTimePickerFormat.Short };

                Label lblEndDate = new Label() { Text = "End Date:", Top = 170, Left = 20, Width = 150 };
                DateTimePicker dtpEndDate = new DateTimePicker() { Top = 170, Left = 180, Width = 280, Format = DateTimePickerFormat.Short };

                Label lblStatus = new Label()
                {
                    Text = "",
                    Top = 220,
                    Left = 20,
                    ForeColor = System.Drawing.Color.Red,
                    Width = 440,
                };

                Button btnOk = new Button()
                {
                    Text = "OK",
                    Top = 270,
                    Left = 280,
                    Width = 90,
                    BackColor = System.Drawing.Color.FromArgb(50, 150, 250),
                    ForeColor = System.Drawing.Color.White
                };

                Button btnCancel = new Button()
                {
                    Text = "Cancel",
                    Top = 270,
                    Left = 380,
                    Width = 90,
                    BackColor = System.Drawing.Color.FromArgb(200, 0, 0),
                    ForeColor = System.Drawing.Color.White
                };

                btnOk.Click += (sender, e) =>
                {
                    if (string.IsNullOrWhiteSpace(txtTaskName.Text))
                    {
                        lblStatus.Text = "Task Name cannot be empty.";
                        return;
                    }

                    if (dtpEndDate.Value < dtpStartDate.Value)
                    {
                        lblStatus.Text = "End Date cannot be earlier than Start Date.";
                        return;
                    }

                    inputForm.DialogResult = DialogResult.OK;
                };

                btnCancel.Click += (sender, e) => inputForm.DialogResult = DialogResult.Cancel;

                inputForm.Controls.AddRange(new Control[] {
                    lblTaskName, txtTaskName,
                    lblTaskType, cboTaskType,
                    lblStartDate, dtpStartDate,
                    lblEndDate, dtpEndDate,
                    lblStatus, btnOk, btnCancel
                });

                if (inputForm.ShowDialog() == DialogResult.OK)
                {
                    CreateTimelinerTask(
                        txtTaskName.Text.Trim(),
                        cboTaskType.SelectedItem.ToString(),
                        dtpStartDate.Value,
                        dtpEndDate.Value
                    );
                }
            }
        }

        public int CreateTimelinerTask(string taskName, string taskType, DateTime plannedStartDate, DateTime plannedEndDate)
        {
            var doc = Autodesk.Navisworks.Api.Application.ActiveDocument;
            var timeliner = doc.GetTimeliner();
            try
            {
                Console.WriteLine($"Attempting to create task: {taskName} of type {taskType}");
                TimelinerTask task = new TimelinerTask
                {
                    DisplayName = taskName,
                    PlannedStartDate = plannedStartDate,
                    PlannedEndDate = plannedEndDate,
                    SimulationTaskTypeName = taskType
                };
                Console.WriteLine("Task object created successfully");

                task.Selection.CopyFrom(new SelectionSourceCollection());
                Console.WriteLine("Selection copied successfully");

                Console.WriteLine("About to execute TaskAddCopy...");
                timeliner.TaskAddCopy(task);
                Console.WriteLine("TaskAddCopy executed successfully");  // If this doesn't print, we know it crashed at TaskAddCopy

                ShowMessage($"Task '{taskName}' added successfully.", "Success", MessageBoxIcon.Information);
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Exception occurred at: {ex.StackTrace}");  // This will show exactly where the error occurred
                Console.WriteLine($"Exception message: {ex.Message}");
                ShowMessage($"Error adding task: {ex.Message}", "Error", MessageBoxIcon.Error);
                return -1;
            }
        }

        private void ShowUpdateTaskForm()
        {
            using (Form updateForm = new Form())
            {
                updateForm.Text = "Update Timeliner Task";
                updateForm.Width = 500;
                updateForm.Height = 450;
                updateForm.FormBorderStyle = FormBorderStyle.FixedDialog;
                updateForm.StartPosition = FormStartPosition.CenterScreen;

                // Task to update
                Label lblTaskToUpdate = new Label() { Text = "Task Name to Update:", Top = 20, Left = 20, Width = 150 };
                TextBox txtTaskToUpdate = new TextBox() { Top = 20, Left = 180, Width = 280 };

                // Optional: New name
                Label lblNewTaskName = new Label() { Text = "New Task Name (Optional):", Top = 70, Left = 20, Width = 150 };
                TextBox txtNewTaskName = new TextBox() { Top = 70, Left = 180, Width = 280 };

                // Checkbox and date picker for start date
                CheckBox chkStartDate = new CheckBox() { Text = "Update Start Date", Top = 120, Left = 20, Width = 150 };
                DateTimePicker dtpStartDate = new DateTimePicker()
                {
                    Top = 120,
                    Left = 180,
                    Width = 280,
                    Format = DateTimePickerFormat.Short,
                    Enabled = false
                };
                chkStartDate.CheckedChanged += (s, e) => dtpStartDate.Enabled = chkStartDate.Checked;

                // Checkbox and date picker for end date
                CheckBox chkEndDate = new CheckBox() { Text = "Update End Date", Top = 170, Left = 20, Width = 150 };
                DateTimePicker dtpEndDate = new DateTimePicker()
                {
                    Top = 170,
                    Left = 180,
                    Width = 280,
                    Format = DateTimePickerFormat.Short,
                    Enabled = false
                };
                chkEndDate.CheckedChanged += (s, e) => dtpEndDate.Enabled = chkEndDate.Checked;

                // Checkbox and combo box for status
                CheckBox chkStatus = new CheckBox() { Text = "Update Status", Top = 220, Left = 20, Width = 150 };
                ComboBox cboTaskStatus = new ComboBox()
                {
                    Top = 220,
                    Left = 180,
                    Width = 280,
                    DropDownStyle = ComboBoxStyle.DropDownList,
                    Enabled = false
                };
                chkStatus.CheckedChanged += (s, e) => cboTaskStatus.Enabled = chkStatus.Checked;

                // Populate task status options
                cboTaskStatus.Items.AddRange(new string[]
                {
            "Not Started",
            "In Progress",
            "Completed",
            "On Hold",
            "Suspended"
                });
                cboTaskStatus.SelectedIndex = 0;

                Label lblStatus = new Label()
                {
                    Text = "",
                    Top = 270,
                    Left = 20,
                    ForeColor = System.Drawing.Color.Red,
                    Width = 440,
                    AutoSize = true
                };

                Button btnUpdate = new Button()
                {
                    Text = "Update Task",
                    Top = 350,
                    Left = 280,
                    Width = 90,
                    BackColor = System.Drawing.Color.FromArgb(50, 150, 250),
                    ForeColor = System.Drawing.Color.White
                };

                Button btnCancel = new Button()
                {
                    Text = "Cancel",
                    Top = 350,
                    Left = 380,
                    Width = 90,
                    BackColor = System.Drawing.Color.FromArgb(200, 0, 0),
                    ForeColor = System.Drawing.Color.White
                };

                btnUpdate.Click += (sender, e) =>
                {
                    if (string.IsNullOrWhiteSpace(txtTaskToUpdate.Text))
                    {
                        lblStatus.Text = "Please enter the name of the task to update.";
                        return;
                    }

                    if (chkEndDate.Checked && chkStartDate.Checked && dtpEndDate.Value < dtpStartDate.Value)
                    {
                        lblStatus.Text = "End Date cannot be earlier than Start Date.";
                        return;
                    }

                    int updateResult = UpdateTimelinerTask(
                        txtTaskToUpdate.Text.Trim(),
                        string.IsNullOrWhiteSpace(txtNewTaskName.Text) ? null : txtNewTaskName.Text.Trim(),
                        chkStartDate.Checked ? dtpStartDate.Value : (DateTime?)null,
                        chkEndDate.Checked ? dtpEndDate.Value : (DateTime?)null,
                        chkStatus.Checked ? cboTaskStatus.SelectedItem.ToString() : null
                    );

                    if (updateResult == 0)
                    {
                        updateForm.DialogResult = DialogResult.OK;
                        updateForm.Close();
                    }
                };

                btnCancel.Click += (sender, e) => updateForm.Close();

                updateForm.Controls.AddRange(new Control[] {
            lblTaskToUpdate, txtTaskToUpdate,
            lblNewTaskName, txtNewTaskName,
            chkStartDate, dtpStartDate,
            chkEndDate, dtpEndDate,
            chkStatus, cboTaskStatus,
            lblStatus, btnUpdate, btnCancel
        });

                updateForm.ShowDialog();
            }
        }

        public int UpdateTimelinerTask(
       string taskToUpdate,
       string newName = null,
       DateTime? newStartDate = null,
       DateTime? newEndDate = null,
       string newStatus = null)
        {
            var doc = Autodesk.Navisworks.Api.Application.ActiveDocument;
            var timeliner = doc.GetTimeliner();
            try
            {
                // Find the task to update
                int taskIndex = -1;
                TimelinerTask originalTask = null;
                for (int i = 0; i < timeliner.Tasks.Count; i++)
                {
                    TimelinerTask currentTask = timeliner.Tasks[i] as TimelinerTask;
                    if (currentTask != null && currentTask.DisplayName == taskToUpdate)
                    {
                        taskIndex = i;
                        originalTask = currentTask;
                        break;
                    }
                }

                if (taskIndex == -1 || originalTask == null)
                {
                    ShowMessage($"Task '{taskToUpdate}' not found.", "Error", MessageBoxIcon.Error);
                    return -1;
                }

                // Create a copy keeping all original values
                TimelinerTask updatedTask = originalTask.CreateCopy();

                // Update only the provided values, keep existing values for others
                updatedTask.DisplayName = newName ?? originalTask.DisplayName;
                updatedTask.PlannedStartDate = newStartDate ?? originalTask.PlannedStartDate;
                updatedTask.PlannedEndDate = newEndDate ?? originalTask.PlannedEndDate;
                updatedTask.SimulationTaskTypeName = originalTask.SimulationTaskTypeName;

                // Update status only if provided, otherwise keep existing status
                if (!string.IsNullOrEmpty(newStatus))
                {
                    switch (newStatus)
                    {
                        case "Not Started":
                            updatedTask.ActualStartDate = null;
                            updatedTask.ActualEndDate = null;
                            break;
                        case "In Progress":
                            updatedTask.ActualStartDate = updatedTask.PlannedStartDate;
                            updatedTask.ActualEndDate = null;
                            break;
                        case "Completed":
                            updatedTask.ActualStartDate = updatedTask.PlannedStartDate;
                            updatedTask.ActualEndDate = updatedTask.PlannedEndDate;
                            break;
                        case "On Hold":
                            updatedTask.ActualStartDate = updatedTask.PlannedStartDate;
                            updatedTask.ActualEndDate = null;
                            break;
                        case "Suspended":
                            updatedTask.ActualStartDate = null;
                            updatedTask.ActualEndDate = null;
                            break;
                        default:
                            ShowMessage($"Invalid task status: {newStatus}", "Error", MessageBoxIcon.Error);
                            return -1;
                    }
                }
                else
                {
                    // Keep original status by maintaining original actual dates
                    updatedTask.ActualStartDate = originalTask.ActualStartDate;
                    updatedTask.ActualEndDate = originalTask.ActualEndDate;
                }

                // Update the task
                timeliner.TaskEdit(taskIndex, updatedTask);

                var selection = originalTask.Selection;
                if (selection != null && selection.GetSelectedItems(doc).Any()) // Ensure selection is valid
                {
                    Autodesk.Navisworks.Api.Color taskColor = null;

                    if (newStatus == "Not Started")
                    {
                        taskColor = Autodesk.Navisworks.Api.Color.FromByteRGB(128, 128, 128); // Gray
                    }
                    else if (newStatus == "In Progress")
                    {
                        taskColor = Autodesk.Navisworks.Api.Color.FromByteRGB(0, 0, 255); // Blue
                    }
                    else if (newStatus == "On Hold")
                    {
                        taskColor = Autodesk.Navisworks.Api.Color.FromByteRGB(128, 0, 128); // Purple
                    }
                    else if (newStatus == "Completed")
                    {
                        taskColor = Autodesk.Navisworks.Api.Color.FromByteRGB(0, 255, 0); // Green
                    }
                    else if (newStatus == "Suspended")
                    {
                        taskColor = Autodesk.Navisworks.Api.Color.FromByteRGB(255, 0, 0); // Red
                    }

                    if (taskColor != null)
                    {
                        doc.Models.OverridePermanentColor(selection.GetSelectedItems(doc), taskColor);
                    }
                    else
                    {
                        // Reset color if status is unrecognized
                        foreach (ModelItem item in selection.GetSelectedItems(doc))
                        {
                            doc.Models.OverridePermanentColor(new List<ModelItem> { item }, null);
                        }
                    }
                }



                ShowMessage($"Task '{taskToUpdate}' updated successfully.", "Success", MessageBoxIcon.Information);
                return 0;
            }
            catch (Exception ex)
            {
                ShowMessage($"Error updating task: {ex.Message}", "Error", MessageBoxIcon.Error);
                return -1;
            }
        }
        private void ShowDeleteTaskForm()
        {
            using (Form deleteForm = new Form())
            {
                deleteForm.Text = "Delete Timeliner Task";
                deleteForm.Width = 400;
                deleteForm.Height = 250;
                deleteForm.FormBorderStyle = FormBorderStyle.FixedDialog;
                deleteForm.StartPosition = FormStartPosition.CenterScreen;

                Label lblSelectTask = new Label() { Text = "Select Task to Delete:", Top = 20, Left = 20, Width = 150 };
                ComboBox cboTasks = new ComboBox()
                {
                    Top = 20,
                    Left = 180,
                    Width = 180,
                    DropDownStyle = ComboBoxStyle.DropDownList
                };

                // Populate tasks dropdown
                var timeliner = Autodesk.Navisworks.Api.Application.ActiveDocument.GetTimeliner();
                var taskNames = new List<string>();

                foreach (SavedItem savedItem in timeliner.Tasks)
                {
                    TimelinerTask currentTask = savedItem as TimelinerTask;
                    if (currentTask != null)
                    {
                        taskNames.Add(currentTask.DisplayName);
                    }
                }

                cboTasks.Items.AddRange(taskNames.ToArray());
                if (cboTasks.Items.Count > 0) cboTasks.SelectedIndex = 0;

                Button btnDelete = new Button()
                {
                    Text = "Delete Task",
                    Top = 120,
                    Left = 180,
                    Width = 90,
                    BackColor = System.Drawing.Color.FromArgb(200, 0, 0),
                    ForeColor = System.Drawing.Color.White
                };

                Label lblStatus = new Label()
                {
                    Text = "",
                    Top = 160,
                    Left = 20,
                    ForeColor = System.Drawing.Color.Red,
                    Width = 350,
                };

                btnDelete.Click += (sender, e) =>
                {
                    if (cboTasks.SelectedItem == null)
                    {
                        lblStatus.Text = "Please select a task to delete.";
                        return;
                    }

                    try
                    {
                        DeleteTimelinerTask(cboTasks.SelectedItem.ToString());
                        deleteForm.Close();
                    }
                    catch (Exception ex)
                    {
                        lblStatus.Text = $"Error: {ex.Message}";
                    }
                };

                deleteForm.Controls.AddRange(new Control[] {
            lblSelectTask, cboTasks,
            btnDelete, lblStatus
        });

                deleteForm.ShowDialog();
            }
        }


        public void DeleteTimelinerTask(string taskToDelete)
        {
            var doc = Autodesk.Navisworks.Api.Application.ActiveDocument;
            DocumentTimeliner timeliner = doc.GetTimeliner();
            int taskIndex = 0;
            try
            {
                foreach (SavedItem savedItem in timeliner.Tasks)
                {
                    TimelinerTask task = savedItem as TimelinerTask;
                    if (task != null && task.DisplayName == taskToDelete)
                    {
                        timeliner.TaskRemoveAt(taskIndex);
                        return; // Exit the loop once the task is removed
                    }
                    taskIndex++;
                }

                MessageBox.Show($"Task '{taskToDelete}' not found.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error removing task: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }



        private void ShowMessage(string message, string caption, MessageBoxIcon icon)
        {
            MessageBox.Show(message, caption, MessageBoxButtons.OK, icon);
        }
    }
}