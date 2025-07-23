using System;
using System.Net;
using System.Threading.Tasks;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace timeliner_Plugin
{
    public class NavisworksServer
    {
        private readonly HttpListener listener;
        private readonly VIS4D plugin;
        private const string Url = "http://localhost:5000/";

        public NavisworksServer(VIS4D pluginInstance)
        {
            plugin = pluginInstance;
            listener = new HttpListener();
            listener.Prefixes.Add(Url);
        }

        public async Task StartServer()
        {
            listener.Start();
            while (true)
            {
                var context = await listener.GetContextAsync();
                _ = HandleRequestAsync(context);
            }
        }

        private async Task HandleRequestAsync(HttpListenerContext context)
        {
            try
            {
                switch (context.Request.HttpMethod)
                {
                    case "POST" when context.Request.Url.PathAndQuery == "/api/timeliner/task":
                        await HandleCreateTask(context);
                        break;
                    case "PUT" when context.Request.Url.PathAndQuery == "/api/timeliner/task/update":
                        await HandleUpdateTask(context);
                        break;
                    case "DELETE" when context.Request.Url.PathAndQuery.StartsWith("/api/timeliner/task/delete/"):
                        await HandleDeleteTask(context);
                        break;
                    default:
                        SendResponse(context, 404, new { error = "Endpoint not found" });
                        break;
                }
            }
            catch (Exception ex)
            {
                SendResponse(context, 500, new { error = ex.Message });
            }
        }

        private async Task HandleCreateTask(HttpListenerContext context)
        {
            System.IO.StreamReader reader = new System.IO.StreamReader(context.Request.InputStream);
            string requestBody = await reader.ReadToEndAsync();
            reader.Dispose();
            var taskData = JsonConvert.DeserializeObject<Dictionary<string, string>>(requestBody);

            var result = plugin.CreateTimelinerTask(
                taskData["taskName"],
                taskData["taskType"],
                DateTime.Parse(taskData["plannedStartDate"]),
                DateTime.Parse(taskData["plannedEndDate"])
            );

            SendResponse(context, result == 0 ? 200 : 500, new { success = result == 0 });
        }

        private async Task HandleUpdateTask(HttpListenerContext context)
        {
            System.IO.StreamReader reader = new System.IO.StreamReader(context.Request.InputStream);
            string requestBody = await reader.ReadToEndAsync();
            reader.Dispose();
            var updateData = JsonConvert.DeserializeObject<UpdateTaskRequest>(requestBody);

            DateTime? newStartDate = null;
            DateTime? newEndDate = null;

            if (!string.IsNullOrEmpty(updateData.Updates.NewStartDate))
            {
                newStartDate = DateTime.Parse(updateData.Updates.NewStartDate);
            }
            if (!string.IsNullOrEmpty(updateData.Updates.NewEndDate))
            {
                newEndDate = DateTime.Parse(updateData.Updates.NewEndDate);
            }

            var result = plugin.UpdateTimelinerTask(
                updateData.TaskName,
                updateData.Updates.NewName,
                newStartDate,
                newEndDate,
                updateData.Updates.NewStatus
            );

            SendResponse(context, result == 0 ? 200 : 500, new { success = result == 0 });
        }

        private async Task HandleDeleteTask(HttpListenerContext context)
        {
            string[] segments = context.Request.Url.Segments;
            string taskName = segments[segments.Length - 1];
            await Task.Run(() => plugin.DeleteTimelinerTask(taskName));
            SendResponse(context, 200, new { success = true });
        }

        private void SendResponse(HttpListenerContext context, int statusCode, object data)
        {
            string response = JsonConvert.SerializeObject(data);
            byte[] buffer = System.Text.Encoding.UTF8.GetBytes(response);

            context.Response.StatusCode = statusCode;
            context.Response.ContentType = "application/json";
            context.Response.ContentLength64 = buffer.Length;
            context.Response.OutputStream.Write(buffer, 0, buffer.Length);
            context.Response.Close();
        }
    }

    public class UpdateTaskRequest
    {
        public string TaskName { get; set; }
        public UpdateData Updates { get; set; }
    }

    public class UpdateData
    {
        public string NewName { get; set; }
        public string NewStartDate { get; set; }
        public string NewEndDate { get; set; }
        public string NewStatus { get; set; }
    }
}