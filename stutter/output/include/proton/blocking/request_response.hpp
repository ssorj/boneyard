namespace proton {
namespace blocking {

class request_response {
  public:
    request_response() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}