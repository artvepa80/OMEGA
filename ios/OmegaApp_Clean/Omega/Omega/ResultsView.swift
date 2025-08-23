import SwiftUI

struct ResultsView: View {
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Image(systemName: "list.bullet.clipboard")
                    .font(.system(size: 60))
                    .foregroundColor(.secondary)
                
                Text("Resultados")
                    .font(.title)
                    .fontWeight(.bold)
                
                Text("Los resultados y estadísticas aparecerán aquí")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                
                Spacer()
            }
            .padding()
            .navigationTitle("Resultados")
        }
    }
}

#Preview {
    ResultsView()
}