import Foundation

enum RevisionChoice: String, CaseIterable, Identifiable {
    case new
    case old

    var id: Self { self }

    var label: String {
        switch self {
        case .new:
            return "Keep New Text"
        case .old:
            return "Keep Old Text"
        }
    }
}
