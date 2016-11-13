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
fa.request("http://10.10.24.71/xgds_image/writeEvent/")
