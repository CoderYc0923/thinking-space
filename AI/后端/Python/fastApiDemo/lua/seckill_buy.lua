-- KEYS[1] = stock key
-- KEYS[2] = bought set key
-- ARGV[1] = user_id

local stock = tonumber(redis.call('GET', KEYS[1]) or '0') -- 获取库存
if stock <= 0 then
    return -1 -- 库存不足
end
if redis.call('SISMEMBER', KEYS[2], ARGV[1]) == 1 then -- 检查是否已购买
    return -2 -- 已购买
end
redis.call('DECR', KEYS[1]) -- 库存减一
redis.call('SADD', KEYS[2], ARGV[1]) -- 记录已购买用户
return 1 -- 购买成功