from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import generic
from django.views.decorators.http import require_POST

from .forms import CommentForm
from .models import Choice, Question, Vote


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        context["comments"] = self.object.comments.select_related("user")
        return context


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def register(request):
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account is ready.")
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)
            return redirect("polls:index")
    else:
        form = UserCreationForm()
    return render(
        request,
        "registration/register.html",
        {"form": form, "next": next_url},
    )


@login_required
@require_POST
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    if Vote.objects.filter(question=question, user=request.user).exists():
        messages.warning(request, "You have already voted on this poll.")
        return redirect("polls:results", pk=question.id)

    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "comment_form": CommentForm(),
                "comments": question.comments.select_related("user"),
                "error_message": "You didn't select a choice.",
            },
        )

    try:
        Vote.objects.create(question=question, choice=selected_choice, user=request.user)
    except IntegrityError:
        messages.warning(request, "You have already voted on this poll.")
        return redirect("polls:results", pk=question.id)

    selected_choice.votes = F("votes") + 1
    selected_choice.save()
    messages.success(request, "Your vote has been recorded!")
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


@login_required
@require_POST
def add_comment(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.question = question
        comment.user = request.user
        comment.save()
        messages.success(request, "Your comment was posted.")
    else:
        messages.error(request, "Please enter a valid comment before submitting.")
    return redirect("polls:detail", pk=question.id)
