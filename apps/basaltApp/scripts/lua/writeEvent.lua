local function waitWlanConnect()
    while 1 do
        local res = fa.ReadStatusReg()
        local a = string.sub(res, 13, 16)
        a = tonumber(a, 16)
        if (bit32.extract(a, 15) == 1) then
            print("connect")
            break
        end
        if (bit32.extract(a, 0) == 1) then
            print("mode Bridge")
            break
        end
        if (bit32.extract(a, 12) == 1) then
            print("mode AP")
            break
        end
        sleep(2000)
    end
end

waitWlanConnect()
headers = {}
args = {}
headers['Authorization'] = 'Basic TODO PYTHON base64.b64encode(username:token)'
headers['X-Test-Header'] = 'I_am_a_header'

args["url"]  = "http://10.10.24.71/xgds_image/rest/writeEvent/"
args["method"] = "GET"
args["headers"] = headers

c = fa.request(args)

print("HTTP/1.1 200 OK\r\n")
print("<HTML>")
print("<HEAD>")
print("<TITLE>Write Event</TITLE>")
print("</HEAD>")
print("<BODY style='font-family:helvetica;'>")
print("<pre>")
print "Write event sent!"
print("Status code:")
print(c)
print("</pre>")
print("</BODY>")
print("</HTML>")
