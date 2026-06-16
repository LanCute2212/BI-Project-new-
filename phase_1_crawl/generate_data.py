import os
import random
import sys
import codecs
import pandas as pd
from datetime import datetime, timedelta

if sys.platform.startswith('win'):
    # Đảm bảo ghi file và in console tiếng Việt không bị lỗi encoding
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        except Exception:
            pass
    if hasattr(sys.stderr, 'buffer'):
        try:
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
        except Exception:
            pass

os.makedirs("data", exist_ok=True)

# Khởi tạo seed để sinh ngẫu nhiên nhưng đồng bộ khi chạy lại
random.seed(42)

PLATFORMS = ["YouTube", "Tinh Tế", "Reddit", "Twitter", "Facebook"]
BRANDS = [
    "VinFast VF 3", 
    "VinFast VF 5", 
    "VinFast VF e34", 
    "VinFast VF 6", 
    "VinFast VF 7", 
    "VinFast VF 8", 
    "VinFast VF 9",
    "BYD Atto 3", 
    "Wuling Hongguang Mini EV", 
    "Xiaomi SU7"
]

BRAND_TO_COMPANY = {
    "VinFast VF 3": "VinFast",
    "VinFast VF 5": "VinFast",
    "VinFast VF e34": "VinFast",
    "VinFast VF 6": "VinFast",
    "VinFast VF 7": "VinFast",
    "VinFast VF 8": "VinFast",
    "VinFast VF 9": "VinFast",
    "BYD Atto 3": "BYD",
    "Wuling Hongguang Mini EV": "Wuling",
    "Xiaomi SU7": "Xiaomi"
}

# Danh sách Celebs/KOLs nổi tiếng ngành xe Việt Nam
CELEBS = [
    {"name": "Xe Hay - Hùng Lâm", "platform": "YouTube", "followers": 1200000},
    {"name": "Tipcar Vietnam", "platform": "YouTube", "followers": 600000},
    {"name": "Autodaily", "platform": "YouTube", "followers": 850000},
    {"name": "Trắng Auto", "platform": "Facebook", "followers": 320000},
    {"name": "Đường 2 Chiều", "platform": "YouTube", "followers": 550000},
    {"name": "Kênh GearUp", "platform": "YouTube", "followers": 420000},
    {"name": "Duy Thẩm Xe Điện", "platform": "Facebook", "followers": 2100000},
    {"name": "Tinh Tế - Xe", "platform": "Tinh Tế", "followers": 180000},
    {"name": "Xế Cưng", "platform": "YouTube", "followers": 750000},
    {"name": "Mê Xe", "platform": "YouTube", "followers": 500000}
]

# Dữ liệu mẫu phân loại theo 6 Khía cạnh (Aspects) và 3 Cảm xúc (Sentiments)
ASPECTS_DATA = {
    "Trạm sạc": {
        "pos": [
            "Hệ thống trạm sạc của {company} phủ khắp nơi, đi tỉnh cực kỳ tiện lợi không lo hết điện.",
            "Sạc nhanh của {company} chỉ mất 25 phút là lên 80% pin, quá nhanh và tiện lợi cho xe {brand}.",
            "Trạm sạc phủ kín từ Bắc vào Nam, đi phượt xuyên Việt bằng xe điện {brand} giờ quá dễ dàng.",
            "Đánh giá cao việc {company} đầu tư mạnh vào trạm sạc, vượt trội hoàn toàn so với các hãng xe khác.",
            "Trạm sạc ở các trung tâm thương mại rất nhiều, vừa đi mua sắm vừa sạc xe {brand} rất tiện.",
            "Đi tỉnh sạc pin dễ dàng nhờ trạm sạc {company} có mặt ở hầu hết các cây xăng dọc quốc lộ.",
            "Trạm sạc nhanh 250kW của {company} sạc cực bốc, chỉ cần uống ly nước là xe {brand} đầy pin đi tiếp.",
            "Số lượng cổng sạc của {company} nhiều khủng khiếp, hiếm khi phải xếp hàng chờ đợi lâu.",
            "Sạc pin xe {brand} ở chung cư giờ cũng tiện hơn nhiều nhờ hãng lắp thêm hàng loạt trụ sạc qua đêm.",
            "Chất lượng dịch vụ tại các điểm sạc của {company} ngày càng tốt, có mái che và camera an ninh."
        ],
        "neg": [
            "Các trạm sạc của {company} ở tỉnh lẻ vẫn còn ít và thưa thớt quá, đi xe {brand} xa vẫn thấy lo.",
            "Nhiều trạm sạc bị xe xăng đỗ chiếm chỗ vô ý thức, đến nơi không sạc được xe {brand} cực kỳ bất tiện.",
            "Trạm sạc nhanh của {brand} thỉnh thoảng bị lỗi kết nối không nhận sạc, mất thời gian chờ đợi.",
            "Chờ đợi sạc pin {brand} ở trạm sạc công cộng vào giờ cao điểm rất mệt mỏi vì phải xếp hàng dài.",
            "Hãng {company} vào Việt Nam mà không tự xây trạm sạc riêng cho {brand}, dùng ké bên thứ ba bất tiện đủ đường.",
            "Đi vào vùng sâu vùng xa tìm trạm sạc {company} mờ mắt không thấy, sạc nhờ ổ điện nhà dân cực kỳ lâu.",
            "Trụ sạc nhanh xe {brand} thỉnh thoảng bị lỗi màn hình hoặc không quét được mã QR thanh toán.",
            "Giá sạc điện ở trạm công cộng {company} bắt đầu tăng cao, tính ra chi phí đi lại không còn rẻ như trước.",
            "Nhiều điểm sạc xe {brand} ban đêm không có đèn chiếu sáng, đi sạc một mình cảm giác hơi sợ.",
            "Tốc độ sạc xe {brand} bị giảm sâu khi có nhiều xe cùng cắm sạc một lúc tại trạm, rất ức chế."
        ],
        "neu": [
            "Cho hỏi bản đồ trạm sạc {company} đã cập nhật thêm các điểm sạc ở khu vực Tây Nguyên chưa?",
            "Không biết {company} khi nào mới liên kết sạc chung trạm sạc cho xe {brand} với các hãng khác?",
            "Mọi người thường sạc pin {brand} ở nhà hay ra trạm sạc công cộng tiện hơn?",
            "Xin review chi tiết về trạm sạc nhanh 250kW của {company} chạy dọc đường cao tốc.",
            "Đang tìm hiểu xem trạm sạc ở khu chung cư Vinhomes cho xe {brand} có dễ đăng ký sạc qua đêm không.",
            "Hỏi về giá điện sạc tại trạm của {company} tính theo block hay tính theo kWh vậy cả nhà?",
            "Có ai gặp tình trạng cắm sạc xe {brand} báo lỗi đỏ nhấp nháy trên trụ sạc chưa?",
            "So sánh số lượng trạm sạc của {company} tại Hà Nội và TP.HCM xem khu vực nào phủ tốt hơn.",
            "Nghe nói hãng sắp ra mắt ứng dụng mới để tìm trạm sạc và đặt chỗ sạc xe {brand} trước đúng không?",
            "Quy trình thanh toán tiền sạc xe {brand} hàng tháng qua ví điện tử có tự động được không?"
        ]
    },
    "Pin & Thuê pin": {
        "pos": [
            "Chính sách thuê pin của {company} hợp lý, không lo chai pin hay hỏng hóc vì được hãng bảo hành thay mới.",
            "Thuê pin xe {brand} giúp giảm giá thành mua xe ban đầu đáng kể, rất phù hợp với ngân sách gia đình.",
            "Pin xe {brand} chạy được quãng đường xa, đi lại cả tuần trong phố mới phải sạc một lần.",
            "Hãng {company} cam kết dung lượng pin xe {brand} dưới 70% là được thay mới miễn phí, quá yên tâm.",
            "Pin công nghệ mới của {brand} sạc mát và bền bỉ, tuổi thọ cao hơn nhiều so với dự kiến.",
            "Gói thuê pin không giới hạn km của {company} cực kỳ có lợi cho những người chạy xe dịch vụ.",
            "Công nghệ pin LFP trên xe {brand} an toàn chống cháy nổ tốt, sạc đầy 100% thoải mái không lo chai.",
            "Chi phí thuê pin cộng tiền điện sạc xe {brand} hàng tháng tính ra vẫn rẻ hơn đổ xăng nhiều.",
            "Dung lượng pin xe {brand} thực tế chạy hỗn hợp được gần 400km, quá đủ cho nhu cầu đi lại bình thường.",
            "Quá trình tháo lắp và thay pin tại xưởng dịch vụ {company} nhanh chóng, nhân viên làm chuyên nghiệp."
        ],
        "neg": [
            "Giá thuê pin hàng tháng của {brand} tăng hơi cao, đi ít thì tính ra không kinh tế bằng xe xăng.",
            "Pin xe {brand} hao nhanh bất thường khi bật điều hòa lạnh sâu vào những ngày hè nắng nóng.",
            "Quãng đường di chuyển thực tế của pin {brand} ngắn hơn khá nhiều so với thông số hãng công bố.",
            "Vẫn lo ngại về vấn đề chai pin xe {brand} sau vài năm sử dụng, chi phí mua đứt pin quá đắt đỏ.",
            "Pin xe {brand} sạc qua đêm tại nhà bằng bộ sạc kèm xe mất quá nhiều thời gian mới đầy.",
            "Chính sách thuê pin mới của {company} có vẻ bắt chẹt người dùng cũ khi đổi xe hoặc sang tên.",
            "Hệ thống quản lý pin (BMS) của {brand} thỉnh thoảng báo lỗi nhiệt độ quá nóng dù mới đi quãng ngắn.",
            "Đi trời mưa ngập nước lo sợ pin {brand} bị vào nước gây chập mạch hỏng hóc, sửa rất tốn kém.",
            "Chính sách cọc pin xe {brand} rườm rà, khi trả pin rút lại tiền cọc chờ đợi làm thủ tục rất lâu.",
            "Pin xe {brand} tụt đột ngột từ 15% xuống 5% trong vài phút, đi đường gặp quả này đứng tim."
        ],
        "neu": [
            "Mọi người cho hỏi chính sách thuê pin mới của {company} áp dụng cho xe mua lại có gì thay đổi không?",
            "Có nên mua đứt pin luôn hay chọn phương án thuê pin hàng tháng cho xe {brand}?",
            "Xin thông số tiêu thụ pin {brand} thực tế khi chạy cao tốc ở tốc độ 100-120 km/h.",
            "Cho mình hỏi chi phí đổi pin hoặc thuê pin trọn gói một tháng của {brand} khoảng bao nhiêu?",
            "Hỏi về tuổi thọ pin xe điện {brand} sau khoảng 100.000 km lăn bánh thực tế.",
            "Gói thuê pin xe {brand} theo tháng giới hạn 1500km có tính lũy kế sang tháng sau không mọi người?",
            "Cho hỏi bộ sạc treo tường tại nhà của {brand} công suất 7kW lắp đặt hết bao nhiêu chi phí?",
            "Pin xe {brand} khi sạc đến 80% thì tự động giảm công suất sạc để bảo vệ pin đúng không?",
            "Hỏi về chính sách bảo hiểm pin xe {brand} khi xảy ra tai nạn đâm đụng ngập nước.",
            "Dòng xe {brand} này dùng chung chuẩn sạc CCS2 với đa số xe điện hiện nay đúng không?"
        ]
    },
    "Phần mềm & Lỗi vặt": {
        "pos": [
            "Hệ thống hỗ trợ lái thông minh ADAS trên {brand} hoạt động rất tốt, giữ làn và bám đuôi xe cực chuẩn.",
            "Bản cập nhật phần mềm mới nhất của {company} đã tối ưu hóa hệ thống, sửa sạch các lỗi vặt trước đây.",
            "Màn hình cảm ứng trung tâm của {brand} mượt mà, kết nối Apple CarPlay không dây rất nhanh và ổn định.",
            "Trợ lý ảo thông minh của {brand} nhận diện giọng nói tiếng Việt ba miền cực kỳ nhạy và chính xác.",
            "Các tính năng thông minh trên {brand} hoạt động trơn tru, nâng cao trải nghiệm lái xe rõ rệt.",
            "Hệ thống cập nhật phần mềm từ xa (OTA) của {brand} rất tiện, chỉ cần bấm nút trên xe là tự nâng cấp.",
            "Trợ lý ảo trên xe {brand} thông minh lắm, nói 'Hey {company}, tôi lạnh' là tự tăng nhiệt độ điều hòa.",
            "Camera 360 độ trên {brand} nét căng, hiển thị mô phỏng 3D xung quanh xe trực quan dễ quan sát.",
            "Bản update firmware mới nhất giúp xe {brand} khởi động nhanh hơn, màn hình không còn độ trễ.",
            "Hệ thống cảm biến xung quanh xe {brand} hoạt động nhạy, cảnh báo va chạm rất chính xác và an toàn."
        ],
        "neg": [
            "Xe {brand} thi thoảng bị lỗi phần mềm vặt, đang đi tự nhiên báo lỗi hệ thống pin ảo làm rất hoang mang.",
            "Màn hình trung tâm {brand} thỉnh thoảng bị đứng hình đen ngóm, phải khóa xe đợi 5 phút reset mới lên.",
            "Hệ thống ADAS trên {brand} thi thoảng báo lỗi camera bị mờ khi đi trời mưa lớn, rất khó chịu.",
            "Phần mềm điều hòa của {brand} bị lỗi lúc mát lúc nóng, cập nhật firmware mấy lần vẫn chưa triệt để.",
            "Lỗi cảm biến áp suất lốp trên {brand} báo sai liên tục dù lốp vẫn căng, gây phiền toái khi lái xe.",
            "Chìa khóa thông minh (Smartkey) xe {brand} chập chờn, nhiều lúc đứng cạnh xe bấm mãi không mở khóa.",
            "Trợ lý ảo của {brand} thỉnh thoảng tự kích hoạt vô cớ dù trong xe không ai gọi, giật cả mình.",
            "Lỗi ảo hệ thống động cơ hiện lên liên tục, mang ra hãng check quét lỗi xóa đi hôm sau lại bị lại.",
            "Kết nối Bluetooth với điện thoại trên xe {brand} chập chờn, nghe nhạc hay bị ngắt quãng nửa chừng.",
            "Hệ thống tự động phanh khẩn cấp của {brand} nhạy quá mức, đôi khi phanh hộc bơ dù vật cản còn rất xa."
        ],
        "neu": [
            "Bản cập nhật phần mềm mới nhất của {brand} có sửa được lỗi báo ảo hệ thống phanh không?",
            "Mọi người hướng dẫn cách reset nhanh màn hình trung tâm của {brand} khi bị treo với ạ.",
            "Hỏi về tính năng tự động đỗ xe của {brand} trên bản cập nhật phần mềm mới có nhạy không?",
            "Có ai gặp tình trạng trợ lý ảo của {brand} không nhận giọng nói khi bật nhạc to không?",
            "Xin hỏi quy trình cập nhật phần mềm xe {brand} lên phiên bản mới nhất tại showroom mất bao lâu.",
            "Có ai biết cách tắt cảnh báo vượt quá tốc độ giới hạn trên màn hình xe {brand} không?",
            "Dòng xe {brand} này có hỗ trợ điều khiển các tính năng qua ứng dụng trên điện thoại không?",
            "Hỏi về bản đồ dẫn đường mặc định trên màn hình xe {brand} có cập nhật cảnh báo kẹt xe thời gian thực?",
            "Mọi người cho hỏi có nên tự cập nhật phần mềm xe {brand} tại nhà hay nên mang ra hãng cho chắc ăn?",
            "Trợ lý ảo thông minh trên xe {brand} có thể kể chuyện cười hoặc tra cứu thông tin thời tiết không?"
        ]
    },
    "Vận hành & Tiện nghi": {
        "pos": [
            "Cảm giác lái của {brand} rất đầm chắc, ôm cua gấp tốc độ cao vẫn cực kỳ ổn định và an tâm.",
            "Động cơ điện {brand} tăng tốc tức thời và mượt mà, không hề bị trễ ga như xe xăng truyền thống.",
            "Khả năng cách âm của {brand} rất tốt, đi trên cao tốc mà cabin vẫn yên tĩnh, êm ái.",
            "Không gian nội thất {brand} rộng rãi thoải mái, hàng ghế sau ngồi rộng chân không bị mỏi.",
            "Điều hòa xe {brand} làm lạnh sâu và nhanh, rất dễ chịu trong thời tiết nắng nóng ở Việt Nam.",
            "Độ đầm chắc của khung gầm xe {brand} vượt trội so với các dòng xe xăng cùng tầm giá.",
            "Hệ thống treo của {brand} triệt tiêu dao động tốt, đi qua đường xấu gồ ghề vẫn rất êm.",
            "Đèn chiếu sáng LED của {brand} siêu sáng, bám đường tốt khi chạy ban đêm trời tối sầm.",
            "Vị trí ngồi lái của {brand} cao ráo, tầm quan sát rộng, gương chiếu hậu chống chói rất tiện.",
            "Hệ thống loa giải trí trên xe {brand} nghe rất hay, bass ấm và treble trong trẻo vượt kỳ vọng."
        ],
        "neg": [
            "Giảm xóc của {brand} hơi cứng, đi qua các gờ giảm tốc trong phố nảy lên rất xóc khó chịu.",
            "Vỏ tôn xe {brand} hơi mỏng nên khả năng cách âm gầm chưa tốt, tiếng lốp dội vào cabin khá ồn.",
            "Nhựa nội thất {brand} có vẻ lỏng lẻo, đi đường xấu nghe tiếng cọt kẹt phát ra từ táp lô.",
            "Vô lăng {brand} hơi nhẹ ở tốc độ cao, cảm giác lái chưa thực sự chân thực và tự tin.",
            "Thiết kế ghế ngồi {brand} hơi đứng, đi hành trình dài tầm 200km là mỏi lưng vô cùng.",
            "Không gian cốp sau xe {brand} hơi nhỏ, đi du lịch cả nhà mang nhiều đồ đạc sắp xếp rất chật chội.",
            "Điều hòa xe {brand} hàng ghế sau hơi yếu, thời tiết nóng đỉnh điểm ngồi sau thấy hơi bí bách.",
            "Mùi da mới trong nội thất xe {brand} khá nồng, đi mấy ngày đầu dễ bị say xe đau đầu.",
            "Cần số nút bấm/xoay của {brand} bố trí hơi bất tiện, thao tác nhanh dễ bị nhầm số.",
            "Gương chiếu hậu xe {brand} góc nhìn hơi hẹp, tạo điểm mù lớn khi muốn chuyển làn trên cao tốc."
        ],
        "neu": [
            "So sánh cảm giác lái giữa chiếc {brand} này với các mẫu xe xăng cùng phân khúc giá.",
            "Ai đi gia đình đông người cho xin đánh giá độ rộng rãi của hàng ghế thứ 3 trên {brand}.",
            "Xin hỏi khoảng sáng gầm xe {brand} có đủ cao để leo lề hay đi đường ngập nước nhẹ không?",
            "Mức độ ồn gầm khi đi trên đường nhựa nhám của {brand} có lớn lắm không mọi người?",
            "Độ đầm chắc của {brand} khi chạy tốc độ 120 km/h trên cao tốc thế nào?",
            "Cho hỏi xe {brand} này có trang bị tính năng sấy gương và làm mát hàng ghế trước không?",
            "Hệ thống treo của {brand} là treo độc lập đa liên kết hay loại dầm xoắn thông thường?",
            "Xin thông số kích thước dài rộng cao chi tiết của dòng xe {brand} này.",
            "Mọi người đánh giá thế nào về chất liệu bọc ghế da nhân tạo trên xe {brand} sau 1 năm sử dụng?",
            "Có ai nâng cấp thêm gioăng cao su chống ồn cho xe {brand} chưa, hiệu quả có rõ rệt không?"
        ]
    },
    "Dịch vụ & Hậu mãi": {
        "pos": [
            "Chính sách bảo hành 10 năm hoặc 200.000 km của {company} giúp người tiêu dùng cực kỳ an tâm mua {brand}.",
            "Dịch vụ cứu hộ pin 24/7 của {company} quá đỉnh, gọi điện hỗ trợ sạc lưu động chỉ sau 30 phút là có mặt.",
            "Nhân viên {company} tại xưởng dịch vụ hỗ trợ chu đáo nhiệt tình, phòng chờ đầy đủ tiện ích sạch sẽ.",
            "Thủ tục bảo hành đổi trả linh kiện hỏng của {brand} nhanh chóng, không gây khó dễ cho khách hàng.",
            "Chương trình chăm sóc khách hàng và tri ân chủ xe {brand} của hãng tổ chức rất chuyên nghiệp.",
            "Dịch vụ sửa chữa lưu động Mobile Service của {company} rất tiện, kỹ thuật đến tận nhà sửa lỗi vặt cho xe.",
            "Hãng {company} tặng nhiều quà tri ân thiết thực cho chủ xe {brand} nhân dịp sinh nhật và lễ tết.",
            "Chi phí bảo dưỡng định kỳ xe {brand} rẻ kinh khủng, rẻ hơn xe xăng gấp 3-4 lần.",
            "Chính sách cam kết mua lại xe cũ của {company} giúp khách hàng yên tâm về tính thanh khoản của {brand}.",
            "Nhân viên tổng đài chăm sóc khách hàng của {company} nói chuyện lịch sự, tiếp nhận ý kiến xử lý nhanh."
        ],
        "neg": [
            "Thời gian chờ đợi bảo dưỡng và sửa chữa {brand} tại xưởng quá lâu do lượng xe đông quá tải.",
            "Nhân viên cứu hộ lưu động {company} đến hơi chậm khi gọi điện hỗ trợ vào ban đêm hoặc thời tiết xấu.",
            "Phụ tùng thay thế chính hãng {brand} khan hiếm, xe nằm xưởng chờ linh kiện cả tháng trời chưa xong.",
            "Thái độ phục vụ của một số nhân viên kỹ thuật {brand} tại showroom chưa thực sự chuyên nghiệp.",
            "Chính sách hỗ trợ đền bù khi xe {brand} gặp lỗi phải nằm xưởng dài ngày làm thủ tục rườm rà.",
            "Gọi điện lên hotline cứu hộ của {company} giờ cao điểm máy bận liên tục không liên lạc được.",
            "Quy trình kiểm tra bảo hành xe {brand} rườm rà, giải trình mãi mới được hãng đồng ý thay thế.",
            "Xưởng dịch vụ của {company} ở tỉnh vẫn còn ít, đi bảo dưỡng phải chạy xe mấy chục km mệt mỏi.",
            "Nhân viên kỹ thuật chẩn đoán sai lỗi xe {brand}, sửa đi sửa lại mấy lần vẫn báo lỗi cũ.",
            "Phòng chờ tại xưởng dịch vụ {company} chật chội, điều hòa yếu và không có nước uống phục vụ khách."
        ],
        "neu": [
            "Cho hỏi chi phí bảo dưỡng định kỳ cấp 1 (khoảng 10.000 km) của {brand} hết bao nhiêu tiền?",
            "Quy trình gọi cứu hộ sạc pin dọc đường của {company} cho xe {brand} hoạt động như thế nào?",
            "Có cần đặt lịch hẹn trước khi mang xe {brand} đi bảo dưỡng định kỳ ở showroom không?",
            "Hỏi về chính sách bảo hành đối với các phụ kiện lắp thêm ngoài hãng của {brand}.",
            "Showroom bảo dưỡng {company} nào ở khu vực TP.HCM làm việc uy tín và nhanh chóng nhất?",
            "Mọi người cho hỏi mang xe {brand} đi bảo dưỡng ở gara ngoài có bị mất quyền bảo hành chính hãng không?",
            "Chính sách đền bù khi xe {brand} nằm xưởng quá 3 ngày hiện tại quy định như thế nào?",
            "Có ai từng dùng dịch vụ sạc pin lưu động của {company} dọc đường chưa, phí dịch vụ tính thế nào?",
            "Hỏi về thời hạn bảo hành của bình ắc quy 12V trên xe {brand} là bao lâu?",
            "Quy trình đăng ký thẻ thành viên VIP để nhận ưu đãi dịch vụ của {company} như thế nào?"
        ]
    },
    "Giá bán & Khuyến mãi": {
        "pos": [
            "Mức giá bán lăn bánh của {brand} cực kỳ hợp lý và cạnh tranh so với các xe xăng cùng phân khúc.",
            "Hãng {company} tung ra nhiều chương trình khuyến mãi tặng voucher sạc pin và ưu đãi thuế trước bạ rất hời.",
            "Chính sách mua xe {brand} trả góp với lãi suất ưu đãi giúp gia đình trẻ dễ dàng sở hữu xe hơn.",
            "Giá xe {brand} giảm sâu nhờ các gói ưu đãi tiên phong, mua đợt đầu tiết kiệm được cả trăm triệu.",
            "Chi phí vận hành hàng tháng của {brand} tính ra rẻ hơn xe xăng rất nhiều, quá kinh tế.",
            "Giá xe {brand} bản thuê pin cực kỳ mềm, tạo điều kiện cho nhiều người tiếp cận ô tô dễ dàng.",
            "Mua xe {brand} đợt này được tặng kèm bộ sạc tại nhà và miễn phí gửi xe tại các khu đô thị lớn, quá hời.",
            "Chính sách hỗ trợ giá cho khách hàng cũ lên đời xe điện {brand} của {company} rất nhân văn.",
            "Giá trị chiếc xe {brand} mang lại hoàn toàn xứng đáng với từng đồng tiền bát gạo bỏ ra.",
            "Thuế tiêu thụ đặc biệt cho xe điện {brand} cực thấp giúp giá xe lăn bánh rẻ hơn hẳn xe xăng cùng hạng."
        ],
        "neg": [
            "Giá bán công bố của {brand} vẫn còn hơi cao so với thu nhập trung bình của đại đa số người dân Việt Nam.",
            "Hãng {company} liên tục thay đổi chính sách giá và chương trình ưu đãi làm người mua xe trước hụt hẫng.",
            "Giá trị bán lại (khấu hao) của xe điện {brand} sau vài năm sử dụng bị rớt giá nhanh hơn xe xăng.",
            "Các chi phí phát sinh như phí gửi xe kèm sạc xe {brand} ở chung cư cộng lại cũng khá tốn kém.",
            "Không có nhiều lựa chọn phiên bản giá rẻ cho những người chỉ có nhu cầu đi xe {brand} tối giản.",
            "Giá pin mua đứt của xe {brand} quá đắt, chiếm gần nửa giá trị của cả chiếc xe.",
            "Chính sách voucher giảm giá của {company} áp dụng lằng nhằng, mua đi bán lại voucher rất phức tạp.",
            "Chi phí bảo hiểm thân vỏ cho xe điện {brand} đắt hơn xe xăng do định giá linh kiện thay thế cao.",
            "Các đại lý bán xe {brand} kèm phụ kiện giá cao, không mua phụ kiện thì thời gian giao xe bị kéo dài.",
            "Giá cước thuê pin tăng lũy tiến theo giá xăng điện làm người tiêu dùng cảm thấy lo lắng lâu dài."
        ],
        "neu": [
            "Đang cân nhắc phương án trả góp 70% giá trị xe {brand} trong vòng 5 năm, lãi suất thế nào?",
            "Xin bảng tính tổng chi phí lăn bánh xe {brand} cụ thể ở Hà Nội và các tỉnh lân cận.",
            "Mức giá thuê pin hiện tại cộng với tiền sạc điện hàng tháng của {brand} có đắt hơn đổ xăng?",
            "Có chương trình khuyến mãi hay tặng quà gì đặc biệt cho khách hàng đặt cọc {brand} sớm không?",
            "Giá xe cũ {brand} hiện tại trên thị trường đang dao động ở mức bao nhiêu?",
            "So sánh tổng chi phí sở hữu (TCO) xe {brand} sau 5 năm sử dụng so với một chiếc xe xăng tương đương.",
            "Gói ưu đãi miễn phí sạc pin 1 năm cho xe {brand} áp dụng tại tất cả các trạm hay chỉ trạm chỉ định?",
            "Giá lăn bánh của {brand} ở tỉnh lẻ có rẻ hơn ở Hà Nội và TP.HCM nhiều không cả nhà?",
            "Nghe nói hãng sắp điều chỉnh tăng giá bán xe {brand} đối với bản mua đứt pin đúng không?",
            "Quy trình áp dụng voucher Vinhomes để thanh toán khi mua xe {brand} được thực hiện như thế nào?"
        ]
    }
}

# Các mẫu câu đặc trưng theo nguồn dữ liệu để tăng tính chân thực
SOURCE_STYLES = {
    "Reddit": [
        "I posted on Vietnam sub: {text}",
        "Discussion: {text} What do you guys think?",
        "{text} Personally, this is a major milestone for EV industry.",
        "{text}"
    ],
    "Twitter": [
        "{text} #{company} #EV #VietNam",
        "{text} #ElectricVehicle #GreenEnergy",
        "{text} #xedien #future",
        "{text}"
    ],
    "Facebook": [
        "[Hội Chủ Xe] {text} Cả nhà cho em ý kiến với ạ!",
        "{text} Tag nhẹ ông bạn vào xem chuẩn bị đổi xe.",
        "{text} Đã cọc em này, lót dép hóng ngày nhận xe.",
        "{text}"
    ],
    "YouTube": [
        "Xem review xong thấy {text} Chắc phải đi lái thử xem sao.",
        "{text} Like cho tinh thần xe điện Việt!",
        "Kênh review chất lượng, {text}",
        "{text}"
    ],
    "Tinh Tế": [
        "Trên tay nhanh: {text}",
        "{text} Chia sẻ từ một người dùng công nghệ lâu năm.",
        "{text} Đúng chất Tinh Tế.",
        "{text}"
    ]
}

def generate_random_comment(brand, platform, sentiment, aspect):
    """
    Sinh ngẫu nhiên một comment tiếng Việt dựa trên khía cạnh, thương hiệu, sắc thái và nền tảng.
    """
    company = BRAND_TO_COMPANY[brand]
    
    # Lấy danh sách mẫu câu dựa trên khía cạnh và sắc thái
    templates = ASPECTS_DATA[aspect]["pos" if sentiment == "Tích cực" else "neg" if sentiment == "Tiêu cực" else "neu"]
    template = random.choice(templates)
    
    # Điền thông tin dòng xe và hãng xe vào mẫu câu
    text = template.format(brand=brand, company=company)
    
    # Áp dụng phong cách viết của từng nền tảng
    style = random.choice(SOURCE_STYLES[platform])
    text = style.format(text=text, company=company).strip()
    
    # Chuẩn hóa khoảng trắng
    text = " ".join(text.split())
    return text

def run_generation(num_mock_comments=1000):
    # Tính toán BASE_DIR thông minh dựa trên việc tệp nằm ở Root hay thư mục con phase
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if "phase_" in os.path.basename(current_dir).lower() or "phase_" in current_dir.lower():
        BASE_DIR = os.path.abspath(os.path.join(current_dir, ".."))
    else:
        BASE_DIR = current_dir

    print("[*] Đang đọc dữ liệu bình luận YouTube thực tế...")
    yt_comments_path = os.path.join(BASE_DIR, "filtered_youtube_comments.csv")
    yt_stats_path = os.path.join(BASE_DIR, "youtube_video_stats.csv")
    
    if not os.path.exists(yt_comments_path) or not os.path.exists(yt_stats_path):
        print(f"[!] Lỗi: Không tìm thấy file dữ liệu YouTube ({yt_comments_path} hoặc {yt_stats_path}).")
        return
        
    df_yt = pd.read_csv(yt_comments_path)
    df_stats = pd.read_csv(yt_stats_path)
    
    # Loại bỏ dòng trống
    df_yt = df_yt.dropna(subset=['text', 'published_at'])
    
    # Tạo từ điển map video_id -> channel_title
    video_id_to_channel = dict(zip(df_stats['video_id'], df_stats['channel_title']))
    
    # Trích xuất thời gian đăng YouTube
    print("[*] Phân tích khoảng thời gian đăng bình luận trên YouTube...")
    yt_dates = []
    for d_str in df_yt['published_at']:
        try:
            yt_dates.append(datetime.strptime(d_str, "%Y-%m-%dT%H:%M:%SZ"))
        except:
            pass
            
    if not yt_dates:
        min_date = datetime.now() - timedelta(days=365)
        max_date = datetime.now()
    else:
        min_date = min(yt_dates)
        max_date = max(yt_dates)
        
    print(f"    - Thời gian bắt đầu: {min_date}")
    print(f"    - Thời gian kết thúc: {max_date}")
    
    # Xử lý dữ liệu YouTube thật
    comments = []
    print(f"[*] Đang xử lý {len(df_yt)} bình luận YouTube thực tế...")
    
    for idx, row in df_yt.iterrows():
        author = str(row['author'])
        try:
            like_count = int(row['like_count'])
        except:
            like_count = 0
        video_id = row['video_id']
        published_at = row['published_at']
        comment_text = row['text']
        
        # Xác định channel name
        channel_name = video_id_to_channel.get(video_id, "YouTube Channel")
        
        # Phân loại Celeb cho YouTube
        # Heuristic: author trùng với tên kênh review xe hoặc like_count >= 100
        author_clean = author.lower().replace("@", "").replace(".", "").strip()
        is_celeb = False
        
        # Check trùng tên kênh review
        for c in CELEBS:
            c_name_clean = c["name"].lower().replace(" ", "").replace("-", "")
            if c_name_clean in author_clean or author_clean in c_name_clean:
                is_celeb = True
                follower_count = c["followers"]
                author = c["name"]
                break
                
        if not is_celeb and like_count >= 100:
            is_celeb = True
            follower_count = random.randint(50000, 1500000)
            
        if not is_celeb:
            author_type = "Regular"
            follower_count = random.randint(5, 500)
        else:
            author_type = "Celeb"
            
        comments.append({
            "comment_id": f"ytb_{idx}",
            "author": author,
            "author_type": author_type,
            "follower_count": follower_count,
            "comment_text": comment_text,
            "published_at": published_at,
            "like_count": like_count,
            "source": channel_name,
            "platform": "YouTube"
        })
        
    # Sinh dữ liệu mô phỏng từ các nền tảng khác
    print(f"[*] Đang sinh thêm {num_mock_comments} bình luận mô phỏng cho Facebook, Twitter, Reddit, Tinh Tế...")
    platforms_mock = ["Facebook", "Twitter", "Reddit", "Tinh Tế"]
    aspects_list = list(ASPECTS_DATA.keys())
    sentiments_pool = ["Tích cực", "Tiêu cực", "Trung lập"]
    
    # 8% Celebs trong số dữ liệu mô phỏng
    celeb_mock_count = int(num_mock_comments * 0.08)
    
    total_sec = int((max_date - min_date).total_seconds())
    
    for i in range(num_mock_comments):
        is_celeb = i < celeb_mock_count
        brand = random.choice(BRANDS)
        sentiment = random.choice(sentiments_pool)
        aspect = random.choice(aspects_list)
        platform = random.choice(platforms_mock)
        
        if is_celeb:
            # Lấy các celebs không thuộc YouTube hoặc fallback
            plat_celebs = [c for c in CELEBS if c["platform"] == platform]
            if not plat_celebs:
                plat_celebs = [c for c in CELEBS if c["platform"] != "YouTube"]
            celeb_profile = random.choice(plat_celebs)
            author = celeb_profile["name"]
            author_type = "Celeb"
            follower_count = celeb_profile["followers"]
        else:
            author = f"User_{platform[:2]}_{random.randint(100, 9999)}"
            author_type = "Regular"
            follower_count = random.randint(10, 500)
            
        # Sinh văn bản bình luận
        comment_text = generate_random_comment(brand, platform, sentiment, aspect)
        
        # Sinh thời gian phân bố đồng bộ trong khoảng min_date -> max_date
        random_sec = random.randint(0, max(1, total_sec))
        published_date = min_date + timedelta(seconds=random_sec)
        published_at = published_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Sinh lượt tương tác ngẫu nhiên
        if author_type == "Celeb":
            like_count = random.randint(100, 5000)
        else:
            if platform == "Facebook":
                like_count = random.randint(5, 300)
            elif platform in ["Twitter", "Reddit"]:
                like_count = random.randint(1, 100)
            else:
                like_count = random.randint(0, 30)
                
        # Tên nguồn cụ thể (sub-source / channel_name)
        if platform == "Facebook":
            source_name = random.choice(["Hội Chủ Xe VinFast [FB]", "Review Ô tô Việt Nam [FB]", "Trà đá Ô tô [FB]"])
        elif platform == "Reddit":
            source_name = random.choice(["r/VinFast", "r/VietNam", "r/ElectricVehicles"])
        elif platform == "Tinh Tế":
            source_name = "Tinh Tế Xe"
        else:
            source_name = "Twitter EV Community"
            
        comments.append({
            "comment_id": f"gen_{platform.lower()[:2]}_{i}",
            "author": author,
            "author_type": author_type,
            "follower_count": follower_count,
            "comment_text": comment_text,
            "published_at": published_at,
            "like_count": like_count,
            "source": source_name,
            "platform": platform
        })
        
    # Tạo DataFrame và sắp xếp theo ngày giờ đăng
    df = pd.DataFrame(comments)
    df['dt'] = pd.to_datetime(df['published_at'])
    df = df.sort_values(by='dt').drop(columns=['dt']).reset_index(drop=True)
    
    # Tính toán BASE_DIR lại để ghi file chính xác
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if "phase_" in os.path.basename(current_dir).lower() or "phase_" in current_dir.lower():
        BASE_DIR = os.path.abspath(os.path.join(current_dir, ".."))
    else:
        BASE_DIR = current_dir
        
    output_path = os.path.join(BASE_DIR, "data", "raw_comments.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[+] Thành công! Đã trộn và ghi {len(df)} dòng dữ liệu thô (YouTube + Mô phỏng) vào: {output_path}")

if __name__ == "__main__":
    run_generation(1000)
